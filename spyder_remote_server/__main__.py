import os
from pathlib import Path
import sys

from jupyterhub.app import JupyterHub

from spyder_remote_server.utils import get_free_port

HERE = Path(os.path.abspath(os.path.dirname(__file__)))

def main():
    """Starts jupyterhub."""
    argv = ["--config", str(HERE / "jupyterhub_config.py")]
    argv.extend(sys.argv[1:])
    if "--port" not in argv:
        port = get_free_port()
        argv.extend(["--port", str(port)])
    if "--show-port" in argv:
        argv.remove("--show-port")
        print(port)
    JupyterHub.launch_instance(argv)

main()
