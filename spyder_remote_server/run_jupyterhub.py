from pathlib import Path
import sys

from jupyterhub.app import JupyterHub

jupyterhub_config_file = Path(__file__).resolve().with_name("jupyterhub_config.py")

def main(argv=[]):
    """Starts jupyterhub."""
    argv = [*argv, "--config", str(jupyterhub_config_file)]

    JupyterHub.launch_instance(argv)

if __name__ == "__main__":
    main(sys.argv[1:])
