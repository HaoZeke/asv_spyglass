"""SBOM-style pairwise inventory diff (eb-stack stack_diff pattern).

Classifies components between two ASV environment inventories:

* unchanged
* added
* removed
* version-bumped

Independent of benchmark timing compare; use alongside ``do_compare``.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from asv_spyglass.inventory import EnvInventory, inventory_from_result_path


class ChangeKind(str, Enum):
    UNCHANGED = "unchanged"
    ADDED = "added"
    REMOVED = "removed"
    VERSION_BUMPED = "version-bumped"

    def as_str(self) -> str:
        return self.value


@dataclass(frozen=True)
class ComponentChange:
    name: str
    kind: ChangeKind
    baseline_version: str | None
    solved_version: str | None
    component_kind: str = "library"


def classify_inventory_diff(
    baseline: EnvInventory,
    solved: EnvInventory,
    *,
    kinds: Iterable[str] | None = None,
) -> list[ComponentChange]:
    """Classify every component name between baseline and solved inventories.

    ``kinds`` filters by component kind (library, runtime, machine, env).
    Default: library + runtime (the package/runtime surface that usually
    explains env-to-env performance deltas). Pass ``None`` kinds to include all.
    """
    allow = None if kinds is None else {k.lower() for k in kinds}
    base_by = {
        c.key(): c
        for c in baseline.components
        if allow is None or c.kind.lower() in allow
    }
    sol_by = {
        c.key(): c
        for c in solved.components
        if allow is None or c.kind.lower() in allow
    }
    names = sorted(set(base_by) | set(sol_by))
    out: list[ComponentChange] = []
    for name in names:
        b = base_by.get(name)
        s = sol_by.get(name)
        if b is None and s is not None:
            out.append(
                ComponentChange(
                    name=s.name,
                    kind=ChangeKind.ADDED,
                    baseline_version=None,
                    solved_version=s.version or "",
                    component_kind=s.kind,
                )
            )
        elif b is not None and s is None:
            out.append(
                ComponentChange(
                    name=b.name,
                    kind=ChangeKind.REMOVED,
                    baseline_version=b.version or "",
                    solved_version=None,
                    component_kind=b.kind,
                )
            )
        elif b is not None and s is not None:
            if (b.version or "") == (s.version or ""):
                kind = ChangeKind.UNCHANGED
            else:
                kind = ChangeKind.VERSION_BUMPED
            out.append(
                ComponentChange(
                    name=b.name,
                    kind=kind,
                    baseline_version=b.version or "",
                    solved_version=s.version or "",
                    component_kind=b.kind,
                )
            )
    return out


def format_inventory_diff_markdown(
    baseline: EnvInventory,
    solved: EnvInventory,
    *,
    kinds: Iterable[str] | None = ("library", "runtime"),
    only_changed: bool = True,
) -> str:
    """Human-reviewable markdown (PR-pasteable), eb-stack stack.diff style."""
    changes = classify_inventory_diff(baseline, solved, kinds=kinds)
    if only_changed:
        changes = [c for c in changes if c.kind != ChangeKind.UNCHANGED]

    counts = {k: 0 for k in ChangeKind}
    for c in classify_inventory_diff(baseline, solved, kinds=kinds):
        counts[c.kind] += 1

    base_label = (
        f"{baseline.machine}/{baseline.env_name}"
        if baseline.machine
        else baseline.env_name
    )
    sol_label = (
        f"{solved.machine}/{solved.env_name}" if solved.machine else solved.env_name
    )

    lines: list[str] = []
    lines.append("# Environment inventory diff\n")
    lines.append(f"Baseline (`{base_label}`) → contender (`{sol_label}`).\n")
    if baseline.commit_hash or solved.commit_hash:
        lines.append(
            f"Commits: `{baseline.commit_hash[:12] or ' - '}` → "
            f"`{solved.commit_hash[:12] or ' - '}`.\n"
        )
    lines.append("## Summary\n")
    lines.append(f"- **unchanged**: {counts[ChangeKind.UNCHANGED]}")
    lines.append(f"- **added**: {counts[ChangeKind.ADDED]}")
    lines.append(f"- **removed**: {counts[ChangeKind.REMOVED]}")
    lines.append(f"- **version-bumped**: {counts[ChangeKind.VERSION_BUMPED]}\n")
    lines.append("## Components\n")

    if not changes:
        lines.append("_No component changes under the current filter._\n")
        return "\n".join(lines)

    lines.append("| Status | Component | Baseline | Contender | Kind |")
    lines.append("|--------|-----------|----------|-----------|------|")
    for c in changes:
        bv = c.baseline_version if c.baseline_version is not None else " - "
        sv = c.solved_version if c.solved_version is not None else " - "
        if bv == "":
            bv = "(empty)"
        if sv == "":
            sv = "(empty)"
        lines.append(
            f"| {c.kind.as_str()} | `{c.name}` | `{bv}` | `{sv}` | {c.component_kind} |"
        )
    lines.append("")
    return "\n".join(lines)


def diff_result_files(
    path_a: str,
    path_b: str,
    *,
    kinds: Iterable[str] | None = ("library", "runtime"),
    only_changed: bool = True,
) -> tuple[str, list[ComponentChange], EnvInventory, EnvInventory]:
    """Convenience: load two result files and format the inventory diff."""
    inv_a = inventory_from_result_path(path_a)
    inv_b = inventory_from_result_path(path_b)
    md = format_inventory_diff_markdown(
        inv_a, inv_b, kinds=kinds, only_changed=only_changed
    )
    changes = classify_inventory_diff(inv_a, inv_b, kinds=kinds)
    return md, changes, inv_a, inv_b
