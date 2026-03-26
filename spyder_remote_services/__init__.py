from spyder_remote_services.app import SpyderRemoteServices
from spyder_remote_services import _version

__version__ = _version.__version__


def _jupyter_server_extension_points():
    """
    Returns a list of dictionaries with metadata describing
    where to find the `_load_jupyter_server_extension` function.
    """
    return [{"module": "spyder_remote_services.app", "app": SpyderRemoteServices}]
