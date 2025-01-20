import dataclasses
import re
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


@dataclasses.dataclass
class PreparedResult:
    """Augmented with information from the benchmarks.json"""

    units: dict
    results: dict
    stats: dict
    versions: dict
    machine_name: str
    env_name: str
    param_names: list

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def to_df(self):
        """
        Converts a PreparedResult object to a Pandas DataFrame,
        exploding the parameters in the keys and flattening the results.
        """

        data = []
        for key, result in self.results.items():
            # Extract benchmark name and parameters
            match = re.match(r"(.+)\((.*)\)", key)
            if match:
                benchmark_name = match.group(1)
                params = match.group(2).split(", ")
            else:
                benchmark_name = key
                params = []

            # Flatten the results tuple
            stats_dict, samples = self.stats[key]

            row = {
                "benchmark_base": benchmark_name,
                "name": key,
                "result": result,
                "units": self.units[key],
                "machine": self.machine_name,
                "env": self.env_name,
                "version": self.versions[key],
                **stats_dict,  # Expand the stats dictionary
                "samples": samples,
            }
            # row.update(dict(zip(["param_" + str(i) for i in range(len(params))], params)))
            # row.update(dict(zip(self.param_names[key], params)))
            # Combine numeric index and parameter name for column names
            row.update(
                dict(
                    zip(
                        [
                            f"param_{i}_{name}"
                            for i, name in enumerate(self.param_names[key])
                        ],
                        params,
                    )
                )
            )
            data.append(row)

        return pd.DataFrame(data)
