import pprint as pp
from pathlib import Path

from approvaltests.approvals import verify
from asv.benchmarks import Benchmarks as ASVBenchmarks
from asv.config import Config as ASVConf



def test_ro_benchmarks(shared_datadir):
    conf_asv = ASVConf()
    conf_asv.results_dir = Path(
        shared_datadir / "asv_samples_a0f29428_benchmarks.json",
    ).parent
    benchmarks = ASVBenchmarks.load(conf_asv)
    verify(pp.pformat(benchmarks))
