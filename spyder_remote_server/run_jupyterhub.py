from pathlib import Path
import sys
import os
import atexit

from jupyterhub.app import JupyterHub

jupyterhub_config_file = Path(__file__).resolve().with_name("jupyterhub_config.py")


def get_running_pid():
    """Check if jupyterhub is running."""
    try:
        with open("jupyterhub.pid", "r") as f:
            pid = int(f.read())
            os.kill(pid, 0)
    except (FileNotFoundError, ProcessLookupError):
        return None
    
    return pid

def get_running_port():
    """Get the port jupyterhub is running on."""
    try:
        with open("jupyterhub.port", "r") as f:
            return int(f.read())
    except FileNotFoundError:
        return None

def cleanup():
    try:
        os.remove("jupyterhub.port")
    except FileNotFoundError:
        pass

def main(argv=[]):
    """Starts jupyterhub."""
    argv = [*argv, "--config", str(jupyterhub_config_file)]

    if get_running_pid():
        print("JupyterHub is already running.")
        return

    cleanup()

    atexit.register(cleanup)

    JupyterHub.launch_instance(argv)


if __name__ == "__main__":
    main(sys.argv[1:])
