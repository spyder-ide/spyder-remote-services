from jupyterhub.auth import NullAuthenticator
from jupyterhub.spawner import LocalProcessSpawner

from spyder_remote_server.utils import get_free_port

# disable hub ui
c.JupyterHub.hub_routespec = "/hub/api"

c.JupyterHub.authenticator_class = NullAuthenticator
c.JupyterHub.spawner_class = LocalProcessSpawner

service_name = "spyder-service"
service_port = get_free_port()

c.JupyterHub.hub_ip = '127.0.0.1'
c.JupyterHub.hub_port = get_free_port()

c.JupyterHub.services = [
    {
        "name": service_name,
        "url": f"http://127.0.0.1:{service_port}",
        "command": ["python", "-m", "spyder_remote_server.run", "--port", str(service_port)],
        "api_token": "GiJ96ujfLpPsq7oatW1IJuER01FbZsgyCM0xH6oMZXDAV6zUZsFy3xQBZakSBo6P",
        "admin": True
    }
]
