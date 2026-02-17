from __future__ import annotations

from pathlib import Path

import tabulate
from asv import results
from asv.commands.compare import _is_result_better, unroll_result
from asv.console import log
from asv.util import human_value
from asv_runner.console import color_print

from asv_spyglass._asv_ro import ReadOnlyASVBenchmarks
from asv_spyglass._num import Ratio
from asv_spyglass.changes import get_change_info
from asv_spyglass.results import ASVBench, PreparedResult, result_iter


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
            for name, value, stats, samples in unroll_result(
                key, params, value, stats, samples
            ):
                result_vals[name] = value
                ss[name] = (stats, samples)
                versions[name] = version
                bench_key = [x for x in self.benchmarks.keys() if key in x][0]
                units[name] = self.benchmarks.get(bench_key, {}).get("unit")
                param_names[name] = self.benchmarks.get(bench_key, {}).get(
                    "param_names"
                )

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
    benchmarks_path: str | Path,
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

    benchmarks = ReadOnlyASVBenchmarks(Path(benchmarks_path)).benchmarks

    preparer = ResultPreparer(benchmarks)
    prepared_1 = preparer.prepare(res_1)
    prepared_2 = preparer.prepare(res_2)

    mname_1 = f"{prepared_1.machine_name}/{prepared_1.env_name}"
    mname_2 = f"{prepared_2.machine_name}/{prepared_2.env_name}"
    machine_env_names = {mname_1, mname_2}

    joint_benchmarks = sorted(
        set(prepared_1.results.keys()) | set(prepared_2.results.keys())
    )

    if split:
        bench = {"green": [], "red": [], "lightgrey": [], "default": []}
    else:
        bench = {"all": []}

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
            f"{mark:1s} {human_value(asv1.time, unit, err=asv1.err):>15s}"
            f"  {human_value(asv2.time, unit, err=asv2.err):>15s}"
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
        if split:
            bench[color].append(split_line)
        else:
            bench["all"].append(split_line)

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

    sections = []
    for key in keys:
        if not bench[key]:
            continue

        if sort == "default":
            pass
        elif sort == "ratio":
            bench[key].sort(key=lambda v: v[3], reverse=True)
        elif sort == "name":
            bench[key].sort(key=lambda v: v[2])
        else:
            raise ValueError("Unknown 'sort'")

        table = tabulate.tabulate(
            bench[key],
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
