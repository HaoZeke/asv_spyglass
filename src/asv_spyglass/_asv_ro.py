import itertools
import json
import re
from pathlib import Path
from typing import Iterator, Union

from asv.util import load_json as asv_json_load

from asv_spyglass._aux import getstrform


class ReadOnlyASVBenchmarks:
    """Read-only holder for a set of ASV benchmarks."""

    api_version = 2

    def __init__(self, benchmarks_file: Path, regex: Union[str, list[str]] = None):
        """
        Initialize and load benchmarks from a JSON file, optionally filtering them.

        Args:
            benchmarks_file (Path): Path to the benchmarks JSON file.
            regex (Union[str, list[str]], optional): Regular expression(s) to filter benchmarks.
                Defaults to None (all benchmarks included).
        """
        d = asv_json_load(getstrform(benchmarks_file), api_version=self.api_version)
        self._all_benchmarks = {}  # Store all benchmarks here
        self._benchmark_selection = {}  # Track selected parameter combinations
        self.filtered_benchmarks = {}  # Store selected benchmarks here

        if not regex:
            regex = []
        if isinstance(regex, str):
            regex = [regex]

        for benchmark in d.values():
            self._all_benchmarks[benchmark["name"]] = benchmark
            if benchmark["params"]:
                self._benchmark_selection[benchmark["name"]] = []
                for idx, param_set in enumerate(
                    itertools.product(*benchmark["params"])
                ):
                    name = f"{benchmark['name']}({', '.join(param_set)})"
                    if not regex or any(re.search(reg, name) for reg in regex):
                        self.filtered_benchmarks[name] = (
                            benchmark  # Store with full name
                        )
                        self._benchmark_selection[benchmark["name"]].append(idx)
            else:
                self._benchmark_selection[benchmark["name"]] = None
                if not regex or any(re.search(reg, benchmark["name"]) for reg in regex):
                    self.filtered_benchmarks[benchmark["name"]] = benchmark

    def __iter__(self) -> Iterator[dict]:
        """Iterate over the filtered benchmarks."""
        return iter(self.filtered_benchmarks.values())

    def __getitem__(self, name: str) -> Union[dict, None]:
        """Get a benchmark by name."""
        return self.filtered_benchmarks.get(name)

    def __repr__(self) -> str:
        """Return a string representation of the filtered benchmarks."""
        import pprint

        pp = pprint.PrettyPrinter()
        return pp.pformat(self.filtered_benchmarks)

    @property
    def benchmark_names(self) -> list[str]:
        """Get a list of benchmark names."""
        return list(self.filtered_benchmarks.keys())

    @property
    def benchmarks(self) -> dict[str, dict]:
        """Get a dictionary of filtered benchmarks."""
        return self.filtered_benchmarks
