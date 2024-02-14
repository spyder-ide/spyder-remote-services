import PyInstaller.__main__
from pathlib import Path

import jupyterhub

HERE = Path(__file__).parent.absolute()
path_to_main = str(HERE / "__main__.py")
path_to_run = str(HERE / "run.py")
path_to_jupyterhub_config = str(HERE / "jupyterhub_config.py")

JUPYTERHUB_PATH = Path(jupyterhub.__file__).parent.absolute()
path_to_alembic = str(JUPYTERHUB_PATH / "alembic")
path_to_alembic_ini = str(JUPYTERHUB_PATH / "alembic.ini")

def install():
    PyInstaller.__main__.run([
        path_to_main,
        '--add-data', f'{path_to_run}:.',
        '--add-data', f'{path_to_jupyterhub_config}:.',
        '--add-data', f'{path_to_alembic}:jupyterhub/alembic',
        '--add-data', f'{path_to_alembic_ini}:jupyterhub',
        '--name', 'spyder-remote-server',
        '--onefile',
        '--noconsole',
    ])
