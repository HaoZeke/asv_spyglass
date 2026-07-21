# Usage Guide

## Installation

You can install `asv-spyglass` using `pip`, `pixi`, or `uv`:

```bash
pip install asv-spyglass
# OR
pixi add asv-spyglass
# OR
uv add asv-spyglass
```

Optional extras:

```bash
# CycloneDX encoding via cyclonedx-python-lib (default install keeps a lightweight encoder)
pip install 'asv-spyglass[sbom]'

# Sphinx docs build dependencies
pip install 'asv-spyglass[doc]'
```

## Basic Comparison

The most common use case is comparing two result files:

```bash
asv-spyglass compare result_before.json result_after.json
```

If you have the `benchmarks.json` file available (usually in the root of your ASV project), you can provide it for enhanced metadata:

```bash
asv-spyglass compare result_before.json result_after.json benchmarks.json
```

## Comparing Multiple Runs

To compare multiple contender runs against a single baseline:

```bash
asv-spyglass compare-many baseline.json contender1.json contender2.json --bconf benchmarks.json
```

## Environment inventory and SBOM-style diffs

ASV result files record the environment surface the run was configured with
(requirements matrix, Python version, machine attributes). Spyglass can dump
that inventory or classify two inventories pairwise
(`added` / `removed` / `version-bumped` / `unchanged`).

Dump one result file:

```bash
asv-spyglass inventory result.json
asv-spyglass inventory result.json --format json
asv-spyglass inventory result.json --format cyclonedx -o env.cdx.json
```

`--format cyclonedx` emits a CycloneDX 1.5-shaped planned inventory. With the
optional `[sbom]` extra installed, encoding uses `cyclonedx-python-lib`;
otherwise a built-in lightweight encoder is used (no extra dependency).

Diff two result files:

```bash
asv-spyglass env-diff result_a.json result_b.json
asv-spyglass env-diff result_a.json result_b.json --all-kinds
asv-spyglass env-diff result_a.json result_b.json --format json --fail-on-change
```

Useful next to `compare` when a timing delta might come from env drift rather
than the code under test.

## DataFrame / CSV export

```bash
asv-spyglass to-df result.json benchmarks.json
asv-spyglass to-df result.json benchmarks.json --csv out.csv
```

## Metadata Handling

`asv-spyglass` can function with only result JSON files. However, providing the `benchmarks.json` file enables:

- **Human-readable units**: Values are shown with appropriate prefixes (e.g., `ns`, `μs`) instead of raw scientific notation.
- **Parameter names**: DataFrame exports will have semantic column names for benchmark parameters.
- **Statistical significance**: Benchmark-specific thresholds are used if defined.

If not explicitly provided, the tool will attempt to automatically find `benchmarks.json` in the parent directory of the first result file.
