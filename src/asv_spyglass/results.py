from __future__ import annotations

import dataclasses
import math
import re
from collections import namedtuple

import polars as pl

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
    param_names: dict

    def __iter__(self):
        for field in dataclasses.fields(self):
            yield getattr(self, field.name)

    def to_df(self) -> pl.DataFrame:
        """Convert to a Polars DataFrame, exploding params and flattening stats."""
        data: list[dict] = []
        for key, result in self.results.items():
            match = re.match(r"(.+)\((.*)\)", key)
            if match:
                benchmark_name = match.group(1)
                params = match.group(2).split(", ") if match.group(2) else []
            else:
                benchmark_name = key
                params = []

            stats_dict, samples = self.stats[key]
            if stats_dict is None:
                stats_dict_maybe_null = {
                    "ci_99_a": None,
                    "ci_99_b": None,
                    "q_25": None,
                    "q_75": None,
                    "number": None,
                    "repeat": None,
                }
            else:
                stats_dict_maybe_null = stats_dict

            row = {
                "benchmark_base": benchmark_name,
                "name": key,
                "result": result,
                "units": self.units[key],
                "machine": self.machine_name,
                "env": self.env_name,
                "version": self.versions[key],
                **stats_dict_maybe_null,
                "samples": samples,
            }
            pnames = self.param_names.get(key)
            if pnames:
                row.update(
                    dict(
                        zip([f"param_{name}" for name in pnames], params, strict=False)
                    )
                )
            data.append(row)

        if not data:
            return pl.DataFrame()
        return pl.from_dicts(data)

    def names_frame(self) -> pl.DataFrame:
        """One-column frame of result keys (String schema even when empty)."""
        return pl.DataFrame(
            {"name": list(self.results.keys())},
            schema={"name": pl.String},
        )


@dataclasses.dataclass(frozen=True)
class ASVBench:
    """Single benchmark value extracted from a PreparedResult."""

    time: float
    err: float | None
    version: str | None
    unit: str | None
    stats_tuple: tuple | None = None

    @classmethod
    def from_prepared_result(cls, name: str, pr: PreparedResult) -> ASVBench:
        time = pr.results.get(name, math.nan)
        stats_entry = pr.stats.get(name)
        if stats_entry and stats_entry[0]:
            from asv_runner.statistics import get_err

            err = get_err(time, stats_entry[0])
        else:
            err = None
        version = pr.versions.get(name)
        unit = pr.units.get(name)
        return cls(
            time=time,
            err=err,
            version=version,
            unit=unit,
            stats_tuple=stats_entry,
        )
