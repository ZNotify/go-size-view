import io
import json
import os
import shutil
import socket
import subprocess
import tarfile
import tempfile
import time
import zipfile
from html.parser import HTMLParser


def get_new_temp_binary() -> str:
    suffix = ".exe" if os.name == "nt" else ""

    temp_dir = tempfile.mkdtemp(prefix="gsa_")

    return os.path.join(temp_dir, f"gsa{suffix}")


def get_project_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def get_covdata_integration_dir():
    return os.path.join(get_project_root(), "covdata", "integration")


def get_covdata_unit_dir():
    return os.path.join(get_project_root(), "covdata", "unit")


def init_dirs():
    paths: list[str] = [
        get_covdata_integration_dir(),
        get_covdata_unit_dir(),
    ]

    for p in paths:
        ensure_dir(p)
        for f in os.listdir(p):
            os.remove(os.path.join(p, f))

    results = os.path.join(get_project_root(), "results")
    clear_folder(results)
    ensure_dir(results)


def clear_folder(folder_path: str) -> None:
    if not os.path.exists(folder_path):
        return

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            os.remove(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def extract_output(p: subprocess.CompletedProcess) -> str:
    ret = ""

    if len(p.stdout) > 0:
        ret += "stdout:\n"
        ret += p.stdout

    if len(p.stderr) > 0:
        ret += "\nstderr:\n"
        ret += p.stderr

    return ret


def load_file_from_tar(f: io.BytesIO, target_name: str) -> bytes:
    with tarfile.open(fileobj=f) as tar:
        for member in tar.getmembers():
            real_name = os.path.basename(member.name)
            if real_name == target_name:
                return tar.extractfile(member).read()
    raise Exception(f"File {target_name} not found in tar.")


def load_file_from_zip(f: io.BytesIO, target_name: str) -> bytes:
    with zipfile.ZipFile(f) as z:
        for name in z.namelist():
            real_name = os.path.basename(name)
            if real_name == target_name:
                return z.read(name)
    raise Exception(f"File {target_name} not found in zip.")


def get_bin_path(name: str) -> str:
    return os.path.join(get_project_root(), "scripts", "bins", name)


def require_go() -> str:
    go = shutil.which("go")
    if go is None:
        raise Exception("Go is not installed. Please install Go and try again.")
    return go


base_time = time.time()


def log(msg: str):
    global base_time
    t = format_time(time.time() - base_time)
    print(f"[{t}] {msg}", flush=True)


def format_time(t: float) -> str:
    return "{:.2f}s".format(t)


def find_unused_port(start_port=20000, end_port=60000):
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            pass
    return None


def run_process(pargs: list[str], name: str, timeout=120, profiler_dir: str = None) -> str:
    env = os.environ.copy()
    env["GOCOVERDIR"] = get_covdata_integration_dir()
    if profiler_dir is not None:
        env["OUTPUT_DIR"] = profiler_dir

    ret = subprocess.run(
        args=pargs,
        env=env, text=True, capture_output=True, cwd=get_project_root(),
        encoding="utf-8", timeout=timeout
    )

    content = extract_output(ret)

    if ret.returncode != 0:
        msg = (f"Failed to run {name}.\n"
               f"Args: {pargs}\n"
               f"Output: {content}\n")
        print(msg)
        raise Exception(f"Failed to run {name}.")

    return content


def get_binaries_path():
    return os.path.join(get_project_root(), "scripts", "binaries.csv")


class DataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_data = False
        self.data = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            for attr in attrs:
                if attr[0] == "type" and attr[1] == "application/json":
                    self.in_data = True

    def handle_data(self, data):
        if self.in_data:
            self.data = data

    def handle_endtag(self, tag):
        if self.in_data:
            self.in_data = False

    def get_data(self):
        return self.data


def assert_html_valid(h: str):
    # parse html
    parser = DataParser()
    parser.feed(h)

    json_data = parser.get_data()
    if json_data is None:
        raise Exception("Failed to find data element in the html.")

    # try load value as json
    try:
        content = json.loads(json_data)
    except json.JSONDecodeError:
        raise Exception("Failed to parse data element as json.")

    # check if the data is correct
    keys = ["name", "size", "packages", "sections"]
    for key in keys:
        if key not in content:
            raise Exception(f"Missing key {key} in the data.")


def dir_is_empty(p: str) -> bool:
    return len(os.listdir(p)) == 0
