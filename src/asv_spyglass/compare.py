import math
from pathlib import Path

import tabulate
from asv import results
from asv.commands.compare import _is_result_better, _isna, unroll_result
from asv.console import log
from asv.util import human_value
from asv_runner.console import color_print
from asv_runner.statistics import get_err

from asv_spyglass._asv_ro import ReadOnlyASVBenchmarks
from dataclasses import dataclass


@dataclass
class PreparedResult:
    units: dict
    results: dict
    stats: dict
    versions: dict
    machine_env_name: str


def result_iter(bdot):
    for key in bdot.get_all_result_keys():
        params = bdot.get_result_params(key)
        result_value = bdot.get_result_value(key, params)
        result_stats = bdot.get_result_stats(key, params)
        result_samples = bdot.get_result_samples(key, params)
        result_version = bdot.benchmark_version.get(key)
        yield (
            key,
            params,
            result_value,
            result_stats,
            result_samples,
            result_version,
            bdot.params["machine"],
            bdot.env_name,
        )


class ResultPreparer:
    """
    Prepares benchmark results for comparison by extracting relevant data
    like units, values, stats, versions, and machine/environment names.
    """

    def __init__(self, benchmarks):
        """
        Initializes ResultPreparer with benchmark data.

        Args:
            benchmarks: Benchmark data used for extracting units.
        """
        self.benchmarks = benchmarks

    def prepare(self, result_data):
        """
        Processes result data and returns extracted information.

        Args:
            result_data: Result data to be processed.

        Returns:
            tuple: A tuple containing units, results, stats, versions,
                   and the machine/environment name.
        """
        units = {}
        results = {}
        ss = {}
        versions = {}

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
                units[name] = self.benchmarks.get(key, {}).get("unit")
                results[name] = value
                ss[name] = (stats, samples)
                versions[name] = version

        return PreparedResult(
            units=units,
            results=results,
            stats=ss,
            versions=versions,
            machine_env_name=machine_env_name,
        )


def do_compare(
    b1,
    b2,
    bdat,
    factor=1.1,
    split=False,
    only_changed=False,
    sort="default",
    machine=None,
    env_spec=None,
    use_stats=True,
):
    # Load results
    res_1 = results.Results.load(b1)
    res_2 = results.Results.load(b2)

    # Initialize benchmarks
    benchmarks = ReadOnlyASVBenchmarks(Path(bdat)).benchmarks

    # Prepare results using the ResultPreparer class
    preparer = ResultPreparer(benchmarks)
    prepared_results_1 = preparer.prepare(res_1)
    prepared_results_2 = preparer.prepare(res_2)
    # Kanged from compare.py

    # Extract data from prepared results
    results_1 = prepared_results_1.results
    results_2 = prepared_results_2.results
    ss_1 = prepared_results_1.stats
    ss_2 = prepared_results_2.stats
    versions_1 = prepared_results_1.versions
    versions_2 = prepared_results_2.versions
    units = prepared_results_1.units

    machine_env_names = set()
    machine_env_names.add(prepared_results_1.machine_env_name)
    machine_env_names.add(prepared_results_2.machine_env_name)

    benchmarks_1 = set(results_1.keys())
    benchmarks_2 = set(results_2.keys())
    joint_benchmarks = sorted(list(benchmarks_1 | benchmarks_2))
    bench = {}

    if split:
        bench["green"] = []
        bench["red"] = []
        bench["lightgrey"] = []
        bench["default"] = []
    else:
        bench["all"] = []

    worsened = False
    improved = False

    for benchmark in joint_benchmarks:
        if benchmark in results_1:
            time_1 = results_1[benchmark]
        else:
            time_1 = math.nan

        if benchmark in results_2:
            time_2 = results_2[benchmark]
        else:
            time_2 = math.nan

        if benchmark in ss_1 and ss_1[benchmark][0]:
            err_1 = get_err(time_1, ss_1[benchmark][0])
        else:
            err_1 = None

        if benchmark in ss_2 and ss_2[benchmark][0]:
            err_2 = get_err(time_2, ss_2[benchmark][0])
        else:
            err_2 = None

        version_1 = versions_1.get(benchmark)
        version_2 = versions_2.get(benchmark)

        if _isna(time_1) or _isna(time_2):
            ratio = "n/a"
            ratio_num = 1e9
        else:
            try:
                ratio_num = time_2 / time_1
                ratio = f"{ratio_num:6.2f}"
            except ZeroDivisionError:
                ratio_num = 1e9
                ratio = "n/a"

        if version_1 is not None and version_2 is not None and version_1 != version_2:
            # not comparable
            color = "lightgrey"
            mark = "x"
        elif time_1 is not None and time_2 is None:
            # introduced a failure
            color = "red"
            mark = "!"
            worsened = True
        elif time_1 is None and time_2 is not None:
            # fixed a failure
            color = "green"
            mark = " "
            improved = True
        elif time_1 is None and time_2 is None:
            # both failed
            color = "default"
            mark = " "
        elif _isna(time_1) or _isna(time_2):
            # either one was skipped
            color = "default"
            mark = " "
        elif _is_result_better(
            time_2,
            time_1,
            ss_2.get(benchmark),
            ss_1.get(benchmark),
            factor,
            use_stats=use_stats,
        ):
            color = "green"
            mark = "-"
            improved = True
        elif _is_result_better(
            time_1,
            time_2,
            ss_1.get(benchmark),
            ss_2.get(benchmark),
            factor,
            use_stats=use_stats,
        ):
            color = "red"
            mark = "+"
            worsened = True
        else:
            color = "default"
            mark = " "

            # Mark statistically insignificant results
            if _is_result_better(
                time_1, time_2, None, None, factor
            ) or _is_result_better(time_2, time_1, None, None, factor):
                ratio = "~" + ratio.strip()

        if only_changed and mark in (" ", "x"):
            continue

        unit = units[benchmark]

        details = "{0:1s} {1:>15s}  {2:>15s} {3:>8s}  ".format(
            mark,
            human_value(time_1, unit, err=err_1),
            human_value(time_2, unit, err=err_2),
            ratio,
        )
        split_line = details.split()
        if len(machine_env_names) > 1:
            benchmark_name = "{} [{}]".format(*benchmark)
        else:
            benchmark_name = benchmark[0]
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

    titles = {}
    titles["green"] = "Benchmarks that have improved:"
    titles["default"] = "Benchmarks that have stayed the same:"
    titles["red"] = "Benchmarks that have got worse:"
    titles["lightgrey"] = "Benchmarks that are not comparable:"
    titles["all"] = "All benchmarks:"

    log.flush()

    for key in keys:
        if len(bench[key]) == 0:
            continue

        if not only_changed:
            color_print("")
            color_print(titles[key])
            color_print("")

        name_1 = False  # commit_names.get(hash_1)
        if name_1:
            name_1 = f"<{name_1}>"
        else:
            name_1 = ""

        name_2 = False  # commit_names.get(hash_2)
        if name_2:
            name_2 = f"<{name_2}>"
        else:
            name_2 = ""

        if sort == "default":
            pass
        elif sort == "ratio":
            bench[key].sort(key=lambda v: v[3], reverse=True)
        elif sort == "name":
            bench[key].sort(key=lambda v: v[2])
        else:
            raise ValueError("Unknown 'sort'")

        print(worsened, improved)
        return tabulate.tabulate(
            bench[key],
            headers=[
                "Change",
                f"Before {name_1}",
                f"After {name_2}",
                "Ratio",
                "Benchmark (Parameter)",
            ],
            tablefmt="github",
        )
