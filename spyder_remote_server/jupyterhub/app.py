import os
from pathlib import Path
from traitlets import Bool, default, observe

from jupyterhub.traitlets import EntryPointType
from jupyterhub.proxy import Proxy
from jupyterhub.app import JupyterHub

from spyder_remote_server.jupyterhub.proxy import SpyderConfigurableHTTPProxy
from spyder_remote_server.jupyterhub.spawner import (
    SpyderLocalProcessSpawner,
)
from spyder_remote_server.utils import generate_token, get_free_port


class SpyderRemoteServer(JupyterHub):
    pid_file = 'jupyterhub.pid'
    port_file = 'jupyterhub.port'
    token_file = 'jupyterhub.token'

    spawner_class = EntryPointType(
        default_value=SpyderLocalProcessSpawner,
        klass=SpyderLocalProcessSpawner,
        entry_point_group='jupyterhub.spawners',
        help="""The class to use for spawning single-user servers.

        Should be a subclass of :class:`jupyterhub.spawner.Spawner`.

        .. versionchanged:: 1.0
            spawners may be registered via entry points,
            e.g. `c.JupyterHub.spawner_class = 'localprocess'`
        """,
    ).tag(config=True)

    set_dynamic_port = Bool(
        True,
        help="""Set the port dynamically.

        Get an available port instead of using the default port
        if no port is provided.
        """,
    ).tag(config=True)

    proxy_class = EntryPointType(
        default_value=SpyderConfigurableHTTPProxy,
        klass=Proxy,
        entry_point_group='jupyterhub.proxies',
        help="""The class to use for configuring the JupyterHub proxy.

        Should be a subclass of :class:`jupyterhub.proxy.Proxy`.

        .. versionchanged:: 1.0
            proxies may be registered via entry points,
            e.g. `c.JupyterHub.proxy_class = 'traefik'`
        """,
    ).tag(config=True)


    @default('services')
    def _services_default(self):
        spyder_token = generate_token()
        with Path(self.token_file).open('w') as f:
            f.write(spyder_token)

        return [
            {
                'name': 'spyder-remote-client',
                'admin': True,
                'api_token': spyder_token,
                'oauth_no_confirm': True,
            },
        ]

    @observe('services')
    def _services_changed(self, change):
        change['new'].insert(0, change['old'][0])

    # @default('load_roles')
    # def _load_roles_default(self):
    #     return [
    #         {
    #             'name': 'spyder-remote-client-role',
    #             'scopes': [
    #                 'admin:users',
    #                 'admin:servers'
    #             ],
    #             'services': [
    #                 'spyder-remote-client',
    #             ],
    #         },
    #     ]

    # @observe('load_roles')
    # def _load_roles_changed(self, change):
    #     change['new'].insert(0, change['old'][0])

    @default('bind_url')
    def _bind_url_default(self):
        proto = 'https' if self.ssl_cert else 'http'
        port = (
            get_free_port()
            if self.set_dynamic_port
            else self.bind_url.split(':')[-1]
        )

        return proto + '://:' + str(port)

    @default('hub_routespec')
    def _default_hub_routespec(self):
        if self.subdomain_host:
            routespec = '/hub/api'
        elif self.base_url[-1] == '/':
            routespec = self.base_url + 'hub/api'
        else:
            routespec = self.base_url + '/hub/api'
        return routespec

    def write_port_file(self):
        port = self.bind_url.split(':')[-1]
        if self.port_file:
            self.log.debug('Writing PORT %s to %s', port, self.port_file)
            with Path(self.port_file).open('w') as f:
                f.write(port)

    async def initialize(self, *args, **kwargs):
        await super().initialize(*args, **kwargs)
        self.write_port_file()

    async def cleanup(self):
        self.log.info('Cleaning up PORT file %s', self.port_file)
        Path(self.port_file).unlink(missing_ok=True)
        self.log.info('Cleaning up TOKEN file %s', self.token_file)
        Path(self.token_file).unlink(missing_ok=True)
        await super().cleanup()

    @classmethod
    def get_running_pid(cls):
        """Check if jupyterhub is running."""
        try:
            with Path(cls.pid_file).open('r') as f:
                pid = int(f.read())
                os.kill(pid, 0)
        except (FileNotFoundError, ProcessLookupError):
            return None

        return pid

    @classmethod
    def get_running_port(cls):
        """Get the port jupyterhub is running on."""
        try:
            with Path(cls.port_file).open('r') as f:
                return int(f.read())
        except FileNotFoundError:
            return None

    @classmethod
    def get_running_token(cls):
        """Get the token jupyterhub is running on."""
        try:
            with Path(cls.token_file).open('r') as f:
                return f.read()
        except FileNotFoundError:
            return None


main = SpyderRemoteServer.launch_instance

if __name__ == '__main__':
    main()
