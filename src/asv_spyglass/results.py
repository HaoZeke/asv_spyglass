from collections import namedtuple

import pandas as pd
from asv import results

from asv_spyglass._asv_ro import ReadOnlyASVBenchmarks

ASVResult = namedtuple(
    "ASVResult",
    [
        "key",
        "params",
        "value",
        "stats",
        "samples",
        "version",
        "machine",
        "env_name",
    ],
)


def result_iter(bdot):
    for key in bdot.get_all_result_keys():
        params = bdot.get_result_params(key)
        result_value = bdot.get_result_value(key, params)
        result_stats = bdot.get_result_stats(key, params)
        result_samples = bdot.get_result_samples(key, params)
        result_version = bdot.benchmark_version.get(key)
        yield ASVResult(
            key,
            params,
            result_value,
            result_stats,
            result_samples,
            result_version,
            bdot.params["machine"],
            bdot.env_name,
        )


def asv_df(bdat: ReadOnlyASVBenchmarks, rb1: results.Results):
    dfl = []
    for key in rb1.get_all_result_keys():
        # From the results object
        params = rb1.get_result_params(key)
        result_value = rb1.get_result_value(key, params)
        result_stats = rb1.get_result_stats(key, params)
        result_samples = rb1.get_result_samples(key, params)
        result_version = rb1.benchmark_version.get(key)
        env_name = rb1.env_name
        machine_name = rb1.params["machine"]

        # Get benchmark information
        bench_key = [x for x in bdat._base_benchmarks if key in x][0]
        units = bdat._base_benchmarks.get(bench_key, {}).get("unit")
        btype = bdat._base_benchmarks.get(bench_key, {}).get("type")
        param_names = bdat._base_benchmarks.get(bench_key, {}).get("param_names")

        res = {
            "key": key,
            "params": params,
            "value": result_value,
            "samples": result_samples,
            "result_stats": result_stats,
            "version": result_version,
            "machine": machine_name,
            "env_name": env_name,
            "units": units,
            "btype": btype,
            "param_names": param_names,
        }
        dfl.append(res)

    df = pd.DataFrame(dfl)

    return df
