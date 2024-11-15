"""Jupyter server example application."""

import os

from jupyter_server.extension.application import ExtensionApp
from jupyter_server.serverapp import ServerApp
from traitlets import Bool, default

from spyder_remote_services.services import handlers
from spyder_remote_services.services.spyder_kernels.patches import (
    patch_maping_kernel_manager,
    patch_main_kernel_handler,
)
from spyder_remote_services.utils import get_free_port


class SpyderServerApp(ServerApp):

    set_dynamic_port = Bool(
        True,
        help="""Set the port dynamically.

        Get an available port instead of using the default port
        if no port is provided.
        """,
    ).tag(config=True)

    @default("port")
    def _port_default(self):
        if self.set_dynamic_port:
            return get_free_port()
        return int(os.getenv(self.port_env, self.port_default_value))


class SpyderRemoteServices(ExtensionApp):
    """A simple jupyter server application."""

    # The name of the extension.
    name = "spyder_remote_services"

    open_browser = False

    serverapp_class = SpyderServerApp

    def initialize_handlers(self):
        """Initialize handlers."""
        self.handlers.extend(handlers)

    def initialize(self):
        super().initialize()
        self.apply_patches()

    def apply_patches(self):
        patch_maping_kernel_manager(self.serverapp.kernel_manager)
        patch_main_kernel_handler(self.serverapp.web_app.default_router)


# -----------------------------------------------------------------------------
# Main entry point
# -----------------------------------------------------------------------------

main = launch_new_instance = SpyderRemoteServices.launch_instance
