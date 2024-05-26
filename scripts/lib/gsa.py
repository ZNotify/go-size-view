import contextlib
import os.path
import shutil
import subprocess

from .utils import log, require_go, get_new_temp_binary, get_project_root


@contextlib.contextmanager
def build_gsa():
    log("Building gsa...")

    go = require_go()
    temp_binary = get_new_temp_binary()
    project_root = get_project_root()

    subprocess.check_output(
        args=[
            go,
            "build",
            "-buildmode=exe",  # since windows use pie by default
            "-cover",
            "-covermode=atomic",
            "-tags",
            "embed,profiler",
            "-o",
            temp_binary,
            f"{project_root}/cmd/gsa",
        ],
        text=True,
        cwd=get_project_root(),
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )

    log("Built gsa.")

    yield temp_binary

    shutil.copyfile(temp_binary, os.path.join(get_project_root(), "results", "gsa"))

@contextlib.contextmanager
def build_pgo_gsa():
    log("Building gsa...")

    go = require_go()
    temp_binary = get_new_temp_binary()
    project_root = get_project_root()

    subprocess.check_output(
        args=[
            go,
            "build",
            "-tags",
            "embed,pgo",
            "-o",
            temp_binary,
            f"{project_root}/cmd/gsa",
        ],
        text=True,
        cwd=get_project_root(),
        stderr=subprocess.STDOUT,
        encoding="utf-8",
    )

    log("Built gsa.")

    yield temp_binary

    os.remove(temp_binary)