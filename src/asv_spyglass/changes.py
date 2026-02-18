"""Enum-based change classification for benchmark comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from asv.commands.compare import (  # type: ignore[import-untyped]
    _is_result_better,
    _isna,
)

from asv_spyglass.results import ASVBench


class ResultColor(str, Enum):
    GREEN = "green"
    RED = "red"
    DEFAULT = "default"
    LIGHTGREY = "lightgrey"


class ResultMark(str, Enum):
    IMPROVED = "-"
    WORSENED = "+"
    INCOMPARABLE = "x"
    FAILURE = "!"
    NONE = " "


class AfterIs(str, Enum):
    BETTER = "better"
    WORSE = "worse"
    SAME = "same"
    INCOMPARABLE = "incomparable"
    FAILED = "failed"
    FIXED = "fixed"


@dataclass(frozen=True)
class ASVChangeInfo:
    """Classification result for a benchmark comparison."""

    color: ResultColor
    mark: ResultMark
    after_is: AfterIs
    row_style: str = ""

    @property
    def is_improved(self) -> bool:
        return self.color == ResultColor.GREEN

    @property
    def is_worsened(self) -> bool:
        return self.color == ResultColor.RED


_ChangeEntry = tuple[
    Callable[[ASVBench, ASVBench, float, bool], bool],
    ASVChangeInfo,
]

CHANGE_INFO: dict[str, _ChangeEntry] = {
    "incomparable": (
        lambda a1, a2, _f, _s: (
            a1.version is not None
            and a2.version is not None
            and a1.version != a2.version
        ),
        ASVChangeInfo(
            ResultColor.LIGHTGREY,
            ResultMark.INCOMPARABLE,
            AfterIs.INCOMPARABLE,
            row_style="dim",
        ),
    ),
    "failure_introduced": (
        lambda a1, a2, _f, _s: a1.time is not None and a2.time is None,
        ASVChangeInfo(
            ResultColor.RED,
            ResultMark.FAILURE,
            AfterIs.FAILED,
            row_style="bold red",
        ),
    ),
    "failure_fixed": (
        lambda a1, a2, _f, _s: a1.time is None and a2.time is not None,
        ASVChangeInfo(
            ResultColor.GREEN,
            ResultMark.NONE,
            AfterIs.FIXED,
            row_style="bold green",
        ),
    ),
    "both_failed": (
        lambda a1, a2, _f, _s: a1.time is None and a2.time is None,
        ASVChangeInfo(
            ResultColor.DEFAULT,
            ResultMark.NONE,
            AfterIs.SAME,
        ),
    ),
    "either_na": (
        lambda a1, a2, _f, _s: _isna(a1.time) or _isna(a2.time),
        ASVChangeInfo(
            ResultColor.DEFAULT,
            ResultMark.NONE,
            AfterIs.SAME,
        ),
    ),
}


def get_change_info(
    asv1: ASVBench,
    asv2: ASVBench,
    factor: float,
    use_stats: bool,
) -> ASVChangeInfo:
    """Classify the change between two benchmark results."""
    for _key, (predicate, info) in CHANGE_INFO.items():
        if predicate(asv1, asv2, factor, use_stats):
            return info

    if _is_result_better(
        asv2.time,
        asv1.time,
        asv2.stats_tuple,
        asv1.stats_tuple,
        factor,
        use_stats=use_stats,
    ):
        return ASVChangeInfo(
            ResultColor.GREEN,
            ResultMark.IMPROVED,
            AfterIs.BETTER,
            row_style="green",
        )

    if _is_result_better(
        asv1.time,
        asv2.time,
        asv1.stats_tuple,
        asv2.stats_tuple,
        factor,
        use_stats=use_stats,
    ):
        return ASVChangeInfo(
            ResultColor.RED,
            ResultMark.WORSENED,
            AfterIs.WORSE,
            row_style="red",
        )

    return ASVChangeInfo(
        ResultColor.DEFAULT,
        ResultMark.NONE,
        AfterIs.SAME,
    )
