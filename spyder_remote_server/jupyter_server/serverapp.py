from jupyter_server.serverapp import ServerApp

from spyder_remote_server.jupyter_server.kernelmanager import SpyderAsyncMappingKernelManager


class SpyderServerApp(ServerApp):
    kernel_manager_class = SpyderAsyncMappingKernelManager


main = launch_new_instance = SpyderServerApp.launch_instance

if __name__ == '__main__':
    main()
