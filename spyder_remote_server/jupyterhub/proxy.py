import sys
from jupyterhub.traitlets import Command

from jupyterhub.proxy import ConfigurableHTTPProxy

from spyder_remote_server.utils import SYS_EXEC


class SpyderConfigurableHTTPProxy(ConfigurableHTTPProxy):
    command = Command(
        [SYS_EXEC, '--configurable-http-proxy'],
        config=True,
        help="""The command to start the proxy""",
    )
