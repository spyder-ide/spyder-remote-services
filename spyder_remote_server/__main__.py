import os
from pathlib import Path

from jupyterhub.app import JupyterHub

HERE = Path(os.path.abspath(os.path.dirname(__file__)))

def start_jupyterhub():
    """Starts jupyterhub."""
    JupyterHub.launch_instance(
        argv=["--config", str(HERE / "jupyterhub_config.py")]
    )

start_jupyterhub()
