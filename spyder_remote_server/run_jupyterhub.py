from pathlib import Path
import sys

from jupyterhub.app import JupyterHub

from spyder_remote_server.utils import get_free_port

jupyterhub_config_file = Path(__file__).resolve().with_name("jupyterhub_config.py")

def main(argv=[]):
    """Starts jupyterhub."""
    argv = [*argv, "--config", str(jupyterhub_config_file)]
    if "--port" not in argv:
        port = get_free_port()
        argv.extend(["--port", str(port)])
    if "--show-port" in argv:
        argv.remove("--show-port")
        print(port)
    
    JupyterHub.launch_instance(argv)

if __name__ == "__main__":
    main(sys.argv[1:])
