from pathlib import Path


def getstrform(pathobj: Path) -> str:
    return str(pathobj.absolute())
