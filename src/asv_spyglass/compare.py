from __future__ import annotations

from pathlib import Path

import polars as pl
import tabulate
from asv import results  # type: ignore[import-untyped]
from asv.commands.compare import (  # type: ignore[import-untyped]
    _is_result_better,
    unroll_result,
)
from asv.console import log  # type: ignore[import-untyped]
from asv.util import human_value  # type: ignore[import-untyped]
from asv_runner.console import color_print  # type: ignore[import-untyped]

from asv_spyglass._asv_ro import ReadOnlyASVBenchmarks
from asv_spyglass._num import Ratio
from asv_spyglass.changes import get_change_info
from asv_spyglass.results import ASVBench, PreparedResult, result_iter


def human_value_fallback(value, unit, err=None):
    """Fallback for human_value when units are missing."""
    if unit:
        return human_value(value, unit, err=err)
    if err:
        return f"{value:.3g}±{err:.1g}"
    return f"{value:.3g}"


def _lookup_bench_meta(benchmarks: dict, key: str) -> dict:
    """Resolve benchmarks.json entry for a result key (exact, then substring)."""
    if key in benchmarks:
        return benchmarks[key]
    for candidate, meta in benchmarks.items():
        if key in candidate:
            return meta
    return {}


def joint_benchmark_names(*prepared: PreparedResult) -> list[str]:
    """Sorted union of result keys across prepared results.

    Uses a set union rather than Polars concat so empty result maps (String vs
    Null schema) never raise SchemaError.
    """
    names: set[str] = set()
    for pr in prepared:
        names.update(pr.results.keys())
    return sorted(names)


class ResultPreparer:
    """Prepares benchmark results for comparison."""

    def __init__(self, benchmarks):
        self.benchmarks = benchmarks

    def prepare(self, result_data) -> PreparedResult:
        units = {}
        result_vals = {}
        ss = {}
        versions = {}
        param_names = {}
        machine_env_name = None

        for (
            key,
            params,
            value,
            stats,
            samples,
            version,
            machine,
            env_name,
        ) in result_iter(result_data):
            machine_env_name = f"{machine}/{env_name}"
            meta = _lookup_bench_meta(self.benchmarks, key)
            for name, value, stats, samples in unroll_result(
                key, params, value, stats, samples
            ):
                result_vals[name] = value
                ss[name] = (stats, samples)
                versions[name] = version
                units[name] = meta.get("unit")
                param_names[name] = meta.get("param_names")

        if machine_env_name is None:
            raise ValueError("No benchmark results found in the result file")

        machine, env_name = machine_env_name.split("/")
        return PreparedResult(
            units=units,
            results=result_vals,
            stats=ss,
            versions=versions,
            machine_name=machine,
            env_name=env_name,
            param_names=param_names,
        )


def do_compare(
    result_before: str,
    result_after: str,
    benchmarks_path: str | Path | None,
    factor: float = 1.1,
    split: bool = False,
    only_changed: bool = False,
    sort: str = "default",
    use_stats: bool = True,
    label_before: str | None = None,
    label_after: str | None = None,
    no_env_label: bool = False,
    only_improved: bool = False,
    only_regressed: bool = False,
) -> tuple[str, bool, bool]:
    """Compare two ASV result files.

    Returns:
        (table_output, has_regressions, has_improvements)
    """
    res_1 = results.Results.load(result_before)
    res_2 = results.Results.load(result_after)

    if benchmarks_path is not None:
        benchmarks_path = Path(benchmarks_path)

    benchmarks = ReadOnlyASVBenchmarks(benchmarks_path).benchmarks

    preparer = ResultPreparer(benchmarks)
    prepared_1 = preparer.prepare(res_1)
    prepared_2 = preparer.prepare(res_2)

    mname_1 = f"{prepared_1.machine_name}/{prepared_1.env_name}"
    mname_2 = f"{prepared_2.machine_name}/{prepared_2.env_name}"
    machine_env_names = {mname_1, mname_2}

    joint_benchmarks = joint_benchmark_names(prepared_1, prepared_2)

    row_records: list[dict] = []
    worsened = False
    improved = False

    for benchmark in joint_benchmarks:
        asv1 = ASVBench.from_prepared_result(benchmark, prepared_1)
        asv2 = ASVBench.from_prepared_result(benchmark, prepared_2)

        ratio = Ratio(t1=asv1.time, t2=asv2.time)

        info = get_change_info(asv1, asv2, factor, use_stats)
        color = info.color.value
        mark = info.mark.value

        if info.is_worsened:
            worsened = True
        if info.is_improved:
            improved = True

        # Mark statistically insignificant results
        if info.after_is.value == "same" and not ratio.is_na:
            if _is_result_better(
                asv1.time, asv2.time, None, None, factor
            ) or _is_result_better(asv2.time, asv1.time, None, None, factor):
                ratio = Ratio(t1=asv1.time, t2=asv2.time, is_insignificant=True)

        if ratio.is_na:
            ratio_str = "n/a"
            ratio_num = 1e9
        else:
            ratio_num = ratio.val
            ratio_str = repr(ratio) if ratio.is_insignificant else f"{ratio.val:6.2f}"

        if only_changed and mark in (" ", "x"):
            continue
        if only_improved and color != "green":
            continue
        if only_regressed and color != "red":
            continue

        unit = asv1.unit or asv2.unit

        details = (
            f"{mark:1s} {human_value_fallback(asv1.time, unit, err=asv1.err):>15s}"
            f"  {human_value_fallback(asv2.time, unit, err=asv2.err):>15s}"
            f" {ratio_str:>8s}  "
        )
        split_line = details.split()
        if no_env_label or len(machine_env_names) <= 1:
            benchmark_name = benchmark
        elif label_before is not None or label_after is not None:
            lbl_1 = label_before if label_before is not None else mname_1
            lbl_2 = label_after if label_after is not None else mname_2
            benchmark_name = f"{benchmark} [{lbl_1} -> {lbl_2}]"
        else:
            benchmark_name = f"{benchmark} [{mname_1} -> {mname_2}]"
        if len(split_line) == 4:
            split_line += [benchmark_name]
        else:
            split_line = [" "] + split_line + [benchmark_name]

        row_records.append(
            {
                "color": color if split else "all",
                "change": split_line[0],
                "before": split_line[1],
                "after": split_line[2],
                "ratio": split_line[3],
                "benchmark": split_line[4],
                "ratio_num": ratio_num,
                "sort_name": split_line[2],  # match legacy name-sort key
            }
        )

    if split:
        keys = ["green", "default", "red", "lightgrey"]
    else:
        keys = ["all"]

    titles = {
        "green": "Benchmarks that have improved:",
        "default": "Benchmarks that have stayed the same:",
        "red": "Benchmarks that have got worse:",
        "lightgrey": "Benchmarks that are not comparable:",
        "all": "All benchmarks:",
    }

    log.flush()

    if not row_records:
        return "", worsened, improved

    frame = pl.DataFrame(row_records)
    if sort == "default":
        pass
    elif sort == "ratio":
        frame = frame.sort("ratio_num", descending=True)
    elif sort == "name":
        frame = frame.sort("sort_name")
    else:
        raise ValueError("Unknown 'sort'")

    sections = []
    for key in keys:
        group = frame.filter(pl.col("color") == key)
        if group.is_empty():
            continue

        table_rows = group.select(
            ["change", "before", "after", "ratio", "benchmark"]
        ).rows()
        table = tabulate.tabulate(
            table_rows,
            headers=[
                "Change",
                "Before",
                "After",
                "Ratio",
                "Benchmark (Parameter)",
            ],
            tablefmt="github",
        )

        if not only_changed:
            color_print("")
            color_print(titles[key])
            color_print("")

        sections.append(table)

    return "\n\n".join(sections), worsened, improved


def do_compare_many(
    baseline_result: str,
    contender_results: list[str],
    benchmarks_path: str | Path | None,
    factor: float = 1.1,
    sort: str = "default",
    use_stats: bool = True,
    labels: list[str] | None = None,
) -> str:
    """Compare multiple ASV result files against a baseline."""
    res_base = results.Results.load(baseline_result)
    res_contenders = [results.Results.load(r) for r in contender_results]

    if benchmarks_path is not None:
        benchmarks_path = Path(benchmarks_path)

    benchmarks_meta = ReadOnlyASVBenchmarks(benchmarks_path).benchmarks
    preparer = ResultPreparer(benchmarks_meta)

    prepared_base = preparer.prepare(res_base)
    prepared_contenders = [preparer.prepare(r) for r in res_contenders]

    mname_base = f"{prepared_base.machine_name}/{prepared_base.env_name}"
    mnames_contenders = [f"{p.machine_name}/{p.env_name}" for p in prepared_contenders]

    if labels:
        display_names = labels
    else:
        display_names = [mname_base] + mnames_contenders

    joint_benchmarks = joint_benchmark_names(prepared_base, *prepared_contenders)

    records: list[dict] = []
    contender_cols = [f"contender_{i}" for i in range(len(prepared_contenders))]

    for benchmark in joint_benchmarks:
        asv_base = ASVBench.from_prepared_result(benchmark, prepared_base)
        unit = asv_base.unit
        record: dict = {
            "benchmark": benchmark,
            "baseline": human_value_fallback(asv_base.time, unit, err=asv_base.err),
        }

        for i, p_cont in enumerate(prepared_contenders):
            asv_cont = ASVBench.from_prepared_result(benchmark, p_cont)
            ratio = Ratio(t1=asv_base.time, t2=asv_cont.time)

            info = get_change_info(asv_base, asv_cont, factor, use_stats)
            mark = info.mark.value

            if ratio.is_na:
                ratio_str = "n/a"
            else:
                # Mark statistically insignificant results
                if info.after_is.value == "same":
                    if _is_result_better(
                        asv_base.time, asv_cont.time, None, None, factor
                    ) or _is_result_better(
                        asv_cont.time, asv_base.time, None, None, factor
                    ):
                        ratio = Ratio(
                            t1=asv_base.time,
                            t2=asv_cont.time,
                            is_insignificant=True,
                        )
                ratio_str = (
                    repr(ratio) if ratio.is_insignificant else f"{ratio.val:6.2f}"
                )

            val_str = human_value_fallback(
                asv_cont.time, asv_cont.unit or unit, err=asv_cont.err
            )
            record[contender_cols[i]] = f"{val_str} ({mark}{ratio_str})"

        records.append(record)

    if not records:
        return ""

    frame = pl.DataFrame(records)
    if sort == "name":
        frame = frame.sort("benchmark")
    # Default order follows joint_benchmark_names (sorted by name)

    select_cols = ["benchmark", "baseline", *contender_cols]
    table_data = frame.select(select_cols).rows()

    headers = ["Benchmark", f"Baseline ({display_names[0]})"]
    for name in display_names[1:]:
        headers.append(f"{name} (Ratio)")

    return tabulate.tabulate(table_data, headers=headers, tablefmt="github")
