from jupyterhub.auth import NullAuthenticator
from jupyterhub.spawner import LocalProcessSpawner

# disable hub ui
c.JupyterHub.hub_routespec = "/hub/api"

c.JupyterHub.authenticator_class = NullAuthenticator
c.JupyterHub.spawner_class = LocalProcessSpawner

c.JupyterHub.admin_users = ["user1"]
c.JupyterHub.admin_access = True

public_host = "http://127.0.0.1:8000"
service_name = "spyder-service"

c.JupyterHub.services = [
    {
        "name": service_name,
        "url": "http://127.0.0.1:10202",
        "command": ["python", "-m", "spyder_remote_server.run", "--port", "10202"],
        "api_token": "GiJ96ujfLpPsq7oatW1IJuER01FbZsgyCM0xH6oMZXDAV6zUZsFy3xQBZakSBo6P",
        "admin": True
    }
]
