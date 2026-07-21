import json
import sys
from pathlib import Path

import click
import polars as pl
from asv import results

from asv_spyglass._asv_ro import ReadOnlyASVBenchmarks
from asv_spyglass.compare import ResultPreparer, do_compare
from asv_spyglass.inventory import (
    inventory_from_result_path,
    inventory_to_cyclonedx,
    write_inventory_json,
)
from asv_spyglass.sbom_diff import (
    ChangeKind,
    classify_inventory_diff,
    format_inventory_diff_markdown,
)


@click.group()
def cli():
    """
    Command-line interface for ASV benchmark analysis.
    """
    pass


@cli.command()
@click.argument("b1", type=click.Path(exists=True), required=True)
@click.argument("b2", type=click.Path(exists=True), required=True)
@click.argument("bconf", type=click.Path(exists=True), required=False)
@click.option(
    "--factor",
    default=1.1,
    show_default=True,
    help="Factor for determining significant changes.",
)
@click.option(
    "--split",
    is_flag=True,
    help="Split output by improvement/regression.",
)
@click.option(
    "--only-changed",
    is_flag=True,
    help="Only show changed benchmarks.",
)
@click.option(
    "--sort",
    type=click.Choice(["default", "ratio", "name"]),
    default="default",
    show_default=True,
    help="Sort output by change, ratio, or name.",
)
@click.option(
    "--label-before",
    default=None,
    help="Custom label for the 'before' environment.",
)
@click.option(
    "--label-after",
    default=None,
    help="Custom label for the 'after' environment.",
)
@click.option(
    "--no-env-label",
    is_flag=True,
    help="Suppress the [machine/env -> machine/env] suffix.",
)
def compare(
    b1,
    b2,
    bconf,
    factor,
    split,
    only_changed,
    sort,
    label_before,
    label_after,
    no_env_label,
):
    """
    Compare two ASV result files.
    """
    if not bconf:
        bconf_path = Path(b1).parent.parent / "benchmarks.json"
        if bconf_path.exists():
            bconf = str(bconf_path)
        else:
            raise click.UsageError(
                "Error: Missing argument 'BCONF'. "
                "Could not find 'benchmarks.json' "
                "automatically. Please provide the "
                "path to your benchmarks.json file."
            )

    import sys

    output, worsened, _ = do_compare(
        b1,
        b2,
        bconf,
        factor,
        split,
        only_changed,
        sort,
        label_before=label_before,
        label_after=label_after,
        no_env_label=no_env_label,
    )
    print(output)
    if worsened:
        sys.exit(1)


@cli.command()
@click.argument("bres", type=click.Path(exists=True), required=True)
@click.argument("bdat", type=click.Path(exists=True), required=True)
@click.option(
    "--csv",
    type=click.Path(),
    help="Save data to csv",
)
def to_df(bres, bdat, csv):
    """
    Generate a dataframe from an ASV result file.
    """
    res = results.Results.load(bres)
    benchdat = ReadOnlyASVBenchmarks(Path(bdat)).benchmarks
    preparer = ResultPreparer(benchdat)
    df = preparer.prepare(res).to_df()
    if csv:
        df.write_csv(csv)
    else:
        with pl.Config(
            tbl_formatting="ASCII_MARKDOWN",
            tbl_hide_column_data_types=True,
            fmt_str_lengths=50,
            tbl_cols=50,
        ):
            click.echo(df)


def _parse_kinds(kind, all_kinds):
    """Resolve --kind / --all-kinds into a kinds filter for classify."""
    if all_kinds:
        return None
    if kind:
        return list(kind)
    return ("library", "runtime")


@cli.command("env-diff")
@click.argument("b1", type=click.Path(exists=True), required=True)
@click.argument("b2", type=click.Path(exists=True), required=True)
@click.option(
    "--kind",
    multiple=True,
    type=click.Choice(["library", "runtime", "machine", "env"]),
    help=(
        "Component kinds to include (repeatable). "
        "Default: library + runtime. Ignored with --all-kinds."
    ),
)
@click.option(
    "--all-kinds",
    is_flag=True,
    help="Include every component kind (library, runtime, machine, env).",
)
@click.option(
    "--include-unchanged",
    is_flag=True,
    help="Keep unchanged components in the table (summary always has full counts).",
)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--fail-on-change",
    is_flag=True,
    help="Exit 1 when any component is added, removed, or version-bumped.",
)
def env_diff(b1, b2, kind, all_kinds, include_unchanged, fmt, fail_on_change):
    """
    SBOM-style environment inventory diff between two ASV result files.

    Extracts packages / runtime pins recorded on each result (requirements,
    python, machine facts) and classifies them as added, removed,
    version-bumped, or unchanged — same pattern as eb-stack stack_diff.
    Independent of timing compare; pair with ``compare`` to explain env deltas.
    """
    kinds = _parse_kinds(kind, all_kinds)
    inv_a = inventory_from_result_path(b1)
    inv_b = inventory_from_result_path(b2)
    changes = classify_inventory_diff(inv_a, inv_b, kinds=kinds)

    if fmt == "markdown":
        click.echo(
            format_inventory_diff_markdown(
                inv_a,
                inv_b,
                kinds=kinds,
                only_changed=not include_unchanged,
            )
        )
    else:
        payload = {
            "baseline": {
                "path": inv_a.source_path,
                "machine": inv_a.machine,
                "env_name": inv_a.env_name,
                "python": inv_a.python,
                "commit_hash": inv_a.commit_hash,
            },
            "contender": {
                "path": inv_b.source_path,
                "machine": inv_b.machine,
                "env_name": inv_b.env_name,
                "python": inv_b.python,
                "commit_hash": inv_b.commit_hash,
            },
            "changes": [
                {
                    "name": c.name,
                    "kind": c.kind.as_str(),
                    "baseline_version": c.baseline_version,
                    "solved_version": c.solved_version,
                    "component_kind": c.component_kind,
                }
                for c in changes
                if include_unchanged or c.kind != ChangeKind.UNCHANGED
            ],
            "summary": {
                k.as_str(): sum(1 for c in changes if c.kind == k) for k in ChangeKind
            },
        }
        click.echo(json.dumps(payload, indent=2, sort_keys=True))

    if fail_on_change and any(c.kind != ChangeKind.UNCHANGED for c in changes):
        sys.exit(1)


@cli.command("inventory")
@click.argument("bres", type=click.Path(exists=True), required=True)
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["json", "cyclonedx", "text"]),
    default="text",
    show_default=True,
    help="Output format (json inventory, minimal CycloneDX 1.5, or text list).",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Write to file instead of stdout.",
)
def inventory_cmd(bres, fmt, output):
    """
    Dump the environment inventory recorded on a single ASV result file.

    Useful as a lock-like snapshot of what the run was configured with
    (requirements matrix, python, machine attributes).
    """
    inv = inventory_from_result_path(bres)

    if fmt == "cyclonedx":
        text = json.dumps(inventory_to_cyclonedx(inv), indent=2, sort_keys=True) + "\n"
    elif fmt == "json":
        if output:
            write_inventory_json(inv, output)
            return
        # stdout path for json
        from dataclasses import asdict

        text = (
            json.dumps(
                {
                    "machine": inv.machine,
                    "env_name": inv.env_name,
                    "python": inv.python,
                    "commit_hash": inv.commit_hash,
                    "source_path": inv.source_path,
                    "components": [asdict(c) for c in inv.components],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    else:
        lines = [
            f"machine: {inv.machine}",
            f"env_name: {inv.env_name}",
            f"python: {inv.python}",
            f"commit: {inv.commit_hash}",
            f"source: {inv.source_path}",
            "components:",
        ]
        for c in inv.components:
            ver = c.version if c.version else "(unpinned)"
            lines.append(f"  [{c.kind}] {c.name} = {ver}")
        text = "\n".join(lines) + "\n"

    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        click.echo(text, nl=False)
