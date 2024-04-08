import argparse

import configurable_http_proxy.cli

from spyder_remote_server import run_jupyterhub, run_service

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--juptyerhub", action="store_true")
    parser.add_argument("--configurable-http-proxy", action="store_true")
    parser.add_argument("--run-service", action="store_true")
    parser.add_argument("--get-running-port", action="store_true")
    parser.add_argument("--get-running-pid", action="store_true")
    args, rest = parser.parse_known_args()
    if args.juptyerhub:
        run_jupyterhub.main(rest)
    elif args.configurable_http_proxy:
        configurable_http_proxy.cli.main(rest)
    elif args.run_service:
        run_service.main(rest)
    elif args.get_running_pid:
        if pid := run_jupyterhub.get_running_pid():
            print(f"PID: {pid}")
        else:
            print("No PID found.")
    elif args.get_running_port:
        if port := run_jupyterhub.get_running_port():
            print(f"Port: {port}")
        else:
            print("No port found.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
