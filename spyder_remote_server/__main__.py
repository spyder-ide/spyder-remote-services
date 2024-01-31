import os
from pathlib import Path
import sys

from jupyterhub.app import JupyterHub

HERE = Path(os.path.abspath(os.path.dirname(__file__)))

def main():
    """Starts jupyterhub."""
    argv = ["--config", str(HERE / "jupyterhub_config.py")]
    argv.extend(sys.argv[1:])
    JupyterHub.launch_instance(argv)

main()
