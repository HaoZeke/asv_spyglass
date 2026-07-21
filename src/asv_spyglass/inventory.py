"""Environment / requirement inventory extracted from ASV result files.

Mirrors the *planned inventory* idea in eb-stack SBOMs: a flat set of
components with versions that can be classified pairwise (added / removed /
version-bumped / unchanged) without needing a full package solver.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from asv import results


@dataclass(frozen=True, order=True)
class Component:
    """One inventory entry (package, interpreter, or machine attribute)."""

    name: str
    version: str = ""
    kind: str = "library"  # library | runtime | machine | env
    purl: str = ""  # optional package URL style id

    def key(self) -> str:
        return self.name.lower()


@dataclass
class EnvInventory:
    """Lock-like snapshot of what an ASV result file was run with."""

    machine: str
    env_name: str
    python: str
    commit_hash: str
    source_path: str
    components: list[Component]

    def by_name(self) -> dict[str, Component]:
        return {c.key(): c for c in self.components}


def _norm_version(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        # ASV sometimes stores empty-string or version lists
        if not v:
            return ""
        return _norm_version(v[0])
    s = str(v).strip()
    return s


def inventory_from_result_path(path: str | Path) -> EnvInventory:
    """Load an ASV result JSON and build an environment inventory."""
    path = Path(path)
    res = results.Results.load(str(path))
    return inventory_from_result(res, source_path=str(path))


def inventory_from_result(res, source_path: str = "") -> EnvInventory:
    """Build inventory from a loaded ``asv.results.Results`` object."""
    machine = ""
    if getattr(res, "params", None):
        machine = str(res.params.get("machine") or "")
    env_name = str(getattr(res, "env_name", "") or "")
    python = str(getattr(res, "python", "") or res.params.get("python") or "")
    commit = str(getattr(res, "commit_hash", "") or "")

    components: list[Component] = []

    # Runtime
    if python:
        components.append(
            Component(
                name="python",
                version=_norm_version(python),
                kind="runtime",
                purl=f"pkg:generic/python@{_norm_version(python)}"
                if python
                else "pkg:generic/python",
            )
        )

    # Requirements matrix (pip/conda pins ASV recorded).
    # asv.results.Results stores this privately as _requirements (no public
    # property); fall back to a public attr if a future asv exposes one.
    reqs = getattr(res, "_requirements", None)
    if reqs is None:
        reqs = getattr(res, "requirements", None)
    reqs = reqs or {}

    # Params mirrors machine facts + often the same requirement names with
    # resolved versions. Prefer a non-empty params value when the requirement
    # pin itself is blank (common for unpinned matrix entries like numpy: "").
    params = getattr(res, "params", None) or {}
    if not isinstance(params, dict):
        params = {}

    if isinstance(reqs, dict):
        for name, ver in sorted(reqs.items(), key=lambda kv: str(kv[0]).lower()):
            n = str(name)
            # strip pip+ / conda channel noise for identity
            identity = n
            if identity.startswith("pip+"):
                identity = identity[4:]
            version = _norm_version(ver)
            if not version and identity in params:
                version = _norm_version(params.get(identity))
            components.append(
                Component(
                    name=identity,
                    version=version,
                    kind="library",
                    purl=f"pkg:pypi/{identity}@{version}"
                    if version
                    else f"pkg:pypi/{identity}",
                )
            )

    # Machine / env facts useful for "why did perf change" attribution
    for key in ("arch", "cpu", "os", "num_cpu", "ram"):
        if key in params and params[key] not in (None, ""):
            components.append(
                Component(
                    name=f"machine.{key}",
                    version=str(params[key]),
                    kind="machine",
                )
            )

    if env_name:
        components.append(Component(name="asv.env_name", version=env_name, kind="env"))

    # Stable order
    components = sorted(components, key=lambda c: (c.kind, c.name.lower()))

    return EnvInventory(
        machine=machine,
        env_name=env_name,
        python=python,
        commit_hash=commit,
        source_path=source_path,
        components=components,
    )


def inventory_to_cyclonedx(inv: EnvInventory) -> dict[str, Any]:
    """Minimal CycloneDX 1.5-shaped document (planned inventory, not installed).

    Deliberately lightweight: no cyclonedx-python dependency. Good enough for
    diff tooling and paste into CI; not a full SBOM compliance claim.
    """
    components = []
    for c in inv.components:
        entry: dict[str, Any] = {
            "type": "library" if c.kind == "library" else "file",
            "name": c.name,
            "version": c.version or "unknown",
        }
        if c.purl:
            entry["purl"] = c.purl
        entry["properties"] = [
            {"name": "asv:component_kind", "value": c.kind},
        ]
        components.append(entry)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "application",
                "name": inv.env_name or "asv-environment",
                "version": inv.commit_hash[:12] or "unknown",
            },
            "properties": [
                {"name": "asv:machine", "value": inv.machine},
                {"name": "asv:env_name", "value": inv.env_name},
                {"name": "asv:python", "value": inv.python},
                {"name": "asv:commit_hash", "value": inv.commit_hash},
                {"name": "asv:source_path", "value": inv.source_path},
                {"name": "asv:document_kind", "value": "planned-inventory-from-result"},
            ],
        },
        "components": components,
    }


def write_inventory_json(inv: EnvInventory, path: str | Path) -> None:
    path = Path(path)
    path.write_text(
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
        + "\n",
        encoding="utf-8",
    )
