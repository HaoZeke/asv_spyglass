import json
import pprint as pp
import re
from pathlib import Path
from typing import Dict, Iterator, List, Union

from asv.util import load_json as asv_json_load

from asv_spyglass._aux import getstrform


class ReadOnlyASVBenchmarks:
    """Read-only holder for a set of ASV benchmarks."""

    api_version = 2

    def __init__(self, benchmarks_file: Path, regex: Union[str, List[str]] = None):
        """
        Initialize and load benchmarks from a JSON file, optionally filtering them.

        Args:
            benchmarks_file (Path): Path to the benchmarks JSON file.
            regex (Union[str, List[str]], optional): Regular expression(s) to filter benchmarks.
                Defaults to None (all benchmarks included).

        Raises:
            UserError: If the benchmarks file is missing or invalid.
        """
        d = asv_json_load(getstrform(benchmarks_file), api_version=self.api_version)
        self._benchmarks = d.values()
        self._filtered_benchmarks = self._filter_benchmarks(regex)

    def __iter__(self) -> Iterator[Dict]:
        """Iterate over the filtered benchmarks."""
        return iter(self._filtered_benchmarks.values())

    def __getitem__(self, name: str) -> Union[Dict, None]:
        """Get a benchmark by name."""
        return self._filtered_benchmarks.get(name)

    def __repr__(self) -> str:
        return pp.pformat(self._filtered_benchmarks)

    @property
    def benchmark_names(self) -> List[str]:
        """Get a list of benchmark names."""
        return list(self._filtered_benchmarks.keys())

    def _filter_benchmarks(
        self, regex: Union[str, List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Filter benchmarks based on provided regular expression(s).

        Args:
            regex (Union[str, List[str]], optional): Regular expression(s) to filter benchmarks.
                Defaults to None (all benchmarks included).

        Returns:
            Dict[str, Dict]: A dictionary containing filtered benchmarks.
        """
        if not regex:
            return {benchmark["name"]: benchmark for benchmark in self._benchmarks}

        if isinstance(regex, str):
            regex = [regex]

        filtered_benchmarks = {}
        for benchmark in self._benchmarks:
            if any(re.search(r, benchmark["name"]) for r in regex):
                filtered_benchmarks[benchmark["name"]] = benchmark
        return filtered_benchmarks
