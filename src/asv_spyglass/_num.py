"""Numerical value types for ASV benchmark comparisons."""

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Ratio:
    """Ratio of two benchmark timings (t2/t1)."""

    t1: float
    t2: float
    is_insignificant: bool = False

    def __post_init__(self):
        if math.isnan(self.t1) or math.isnan(self.t2):
            object.__setattr__(self, "_val", math.nan)
        elif self.t1 == 0:
            object.__setattr__(self, "_val", math.inf)
        else:
            object.__setattr__(self, "_val", self.t2 / self.t1)

    @property
    def val(self) -> float:
        return self._val

    @property
    def is_na(self) -> bool:
        return math.isnan(self._val) or math.isinf(self._val)

    def __repr__(self) -> str:
        if self.is_na:
            return "n/a"
        prefix = "~" if self.is_insignificant else ""
        return f"{prefix}{self._val:.2f}"
