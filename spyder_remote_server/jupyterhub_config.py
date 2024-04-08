import sys

from jupyterhub.auth import NullAuthenticator
from jupyterhub.spawner import LocalProcessSpawner

from spyder_remote_server.utils import get_free_port

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    spyder_remote_server_exec = sys.executable
else:
    spyder_remote_server_exec = "spyder-remote-server"

# disable hub ui
c.JupyterHub.hub_routespec = "/hub/api"

c.JupyterHub.authenticator_class = NullAuthenticator
c.JupyterHub.spawner_class = LocalProcessSpawner

c.ConfigurableHTTPProxy.command = [spyder_remote_server_exec, "--configurable-http-proxy"]

service_name = "spyder-service"
service_port = get_free_port()
jupyterhub_hub_port = get_free_port()
jupyterhub_port = get_free_port()

with open("jupyterhub.port", "w") as f:
    f.write(str(jupyterhub_port))

c.JupyterHub.hub_port = jupyterhub_hub_port

c.JupyterHub.port = jupyterhub_port
c.JupyterHub.pid_file = "jupyterhub.pid"

c.JupyterHub.services = [
    {
        "name": service_name,
        "url": f"http://127.0.0.1:{service_port}",
        "command": [spyder_remote_server_exec, "--run-service", "--port", str(service_port)],
        "api_token": "GiJ96ujfLpPsq7oatW1IJuER01FbZsgyCM0xH6oMZXDAV6zUZsFy3xQBZakSBo6P",
        "admin": True
    }
]
