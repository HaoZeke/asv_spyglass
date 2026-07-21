"""Tests for environment inventory extraction and SBOM-style diffs."""

from asv_spyglass._aux import getstrform
from asv_spyglass.inventory import (
    inventory_from_result_path,
    inventory_to_cyclonedx,
)
from asv_spyglass.sbom_diff import (
    ChangeKind,
    classify_inventory_diff,
    format_inventory_diff_markdown,
)


def test_inventory_from_result_with_numpy(shared_datadir):
    inv = inventory_from_result_path(
        getstrform(shared_datadir / "d6b286b8-virtualenv-py3.12-numpy.json")
    )
    assert inv.machine == "rgx1gen11"
    assert inv.env_name == "virtualenv-py3.12-numpy"
    assert inv.python == "3.12"
    assert inv.commit_hash.startswith("d6b286b8")
    by = inv.by_name()
    assert "python" in by
    assert by["python"].kind == "runtime"
    assert by["python"].version == "3.12"
    assert "numpy" in by
    assert by["numpy"].kind == "library"
    assert by["asv.env_name"].kind == "env"
    assert by["machine.arch"].version == "x86_64"


def test_inventory_without_requirements(shared_datadir):
    inv = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12.json")
    )
    by = inv.by_name()
    assert "numpy" not in by
    assert "python" in by


def test_classify_numpy_added(shared_datadir):
    base = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12.json")
    )
    solved = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12-numpy.json")
    )
    changes = classify_inventory_diff(base, solved, kinds=("library", "runtime"))
    by_name = {c.name: c for c in changes}
    assert by_name["numpy"].kind == ChangeKind.ADDED
    assert by_name["python"].kind == ChangeKind.UNCHANGED


def test_classify_numpy_removed(shared_datadir):
    base = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12-numpy.json")
    )
    solved = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12.json")
    )
    changes = classify_inventory_diff(base, solved, kinds=("library",))
    by_name = {c.name: c for c in changes}
    assert by_name["numpy"].kind == ChangeKind.REMOVED


def test_classify_python_version_bumped(shared_datadir):
    base = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-conda-py3.11-numpy.json")
    )
    solved = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12-numpy.json")
    )
    changes = classify_inventory_diff(base, solved, kinds=("runtime",))
    by_name = {c.name: c for c in changes}
    assert by_name["python"].kind == ChangeKind.VERSION_BUMPED
    assert by_name["python"].baseline_version == "3.11"
    assert by_name["python"].solved_version == "3.12"


def test_classify_all_kinds_includes_env(shared_datadir):
    base = inventory_from_result_path(
        getstrform(shared_datadir / "d6b286b8-virtualenv-py3.12-numpy.json")
    )
    solved = inventory_from_result_path(
        getstrform(shared_datadir / "d6b286b8-rattler-py3.12-numpy.json")
    )
    changes = classify_inventory_diff(base, solved, kinds=None)
    by_name = {c.name: c for c in changes}
    assert "asv.env_name" in by_name
    assert by_name["asv.env_name"].kind == ChangeKind.VERSION_BUMPED
    assert by_name["asv.env_name"].baseline_version == "virtualenv-py3.12-numpy"
    assert by_name["asv.env_name"].solved_version == "rattler-py3.12-numpy"


def test_format_markdown_only_changed(shared_datadir):
    base = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12.json")
    )
    solved = inventory_from_result_path(
        getstrform(shared_datadir / "a0f29428-virtualenv-py3.12-numpy.json")
    )
    md = format_inventory_diff_markdown(base, solved, only_changed=True)
    assert "# Environment inventory diff" in md
    assert "**added**" in md
    assert "`numpy`" in md
    assert "unchanged" in md  # summary line
    # python is unchanged and only_changed=True so no python row in table
    assert "| unchanged | `python`" not in md


def test_cyclonedx_shape(shared_datadir):
    inv = inventory_from_result_path(
        getstrform(shared_datadir / "d6b286b8-rattler-py3.12-numpy.json")
    )
    bom = inventory_to_cyclonedx(inv)
    assert bom["bomFormat"] == "CycloneDX"
    assert bom["specVersion"] == "1.5"
    assert bom["metadata"]["component"]["name"] == "rattler-py3.12-numpy"
    names = {c["name"] for c in bom["components"]}
    assert "python" in names
    assert "numpy" in names
    numpy_entry = next(c for c in bom["components"] if c["name"] == "numpy")
    assert numpy_entry["purl"].startswith("pkg:pypi/numpy")
