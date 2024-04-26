import argparse

import configurable_http_proxy.cli

from spyder_remote_server.jupyterhub.app import (
    SpyderRemoteServer,
    main as jupyterhub_main,
)
from spyder_remote_server.jupyterhub.singleuser import main as singleuser_main


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--jupyterhub', action='store_true')
    parser.add_argument('--jupyterhub-singleuser', action='store_true')
    parser.add_argument('--configurable-http-proxy', action='store_true')
    parser.add_argument('--get-running-port', action='store_true')
    parser.add_argument('--get-running-pid', action='store_true')
    parser.add_argument('--get-running-token', action='store_true')
    args, rest = parser.parse_known_args(argv)
    if args.jupyterhub:
        jupyterhub_main(rest)
    elif args.jupyterhub_singleuser:
        singleuser_main(rest)
    elif args.configurable_http_proxy:
        configurable_http_proxy.cli.main(rest)
    elif args.get_running_pid:
        if pid := SpyderRemoteServer.get_running_pid():
            print(f'PID: {pid}')
        else:
            print('No PID found.')
    elif args.get_running_port:
        if port := SpyderRemoteServer.get_running_port():
            print(f'Port: {port}')
        else:
            print('No port found.')
    elif args.get_running_token:
        if token := SpyderRemoteServer.get_running_token():
            print(f'Token: {token}')
        else:
            print('No token found.')
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
