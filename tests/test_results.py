from pathlib import Path

from approvaltests.approvals import verify
import pprint as pp

from asv import results
from asv_spyglass.compare import result_iter


# Kanged from rgpycrumbs
def getstrform(pathobj):
    return str(pathobj.absolute())


def test_result_iter(shared_datadir):
    bdot = results.Results.load(
        getstrform(shared_datadir / "a0f29428-conda-py3.11-numpy.json")
    )
    verify(pp.pformat(list(result_iter(bdot))))
