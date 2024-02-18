import argparse

import configurable_http_proxy.cli

from spyder_remote_server import run_jupyterhub, run_service

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--juptyerhub", action="store_true")
    parser.add_argument("--configurable-http-proxy", action="store_true")
    parser.add_argument("--run-service", action="store_true")
    args, rest = parser.parse_known_args()
    if args.juptyerhub:
        run_jupyterhub.main(rest)
    elif args.configurable_http_proxy:
        configurable_http_proxy.cli.main(rest)
    elif args.run_service:
        run_service.main(rest)
    else:
        parser.print_help()

main()
