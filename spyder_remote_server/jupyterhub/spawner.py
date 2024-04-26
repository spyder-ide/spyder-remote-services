from jupyterhub.spawner import LocalProcessSpawner

from spyder_remote_server.utils import SYS_EXEC


class SpyderLocalProcessSpawner(LocalProcessSpawner):
    cmd = [SYS_EXEC, '--jupyterhub-singleuser']
