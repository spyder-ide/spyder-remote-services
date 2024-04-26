from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager



class SpyderAsyncMappingKernelManager(AsyncMappingKernelManager):
    kernel_manager_class = 'spyder_remote_server.jupyter_client.manager.SpyderAsyncIOLoopKernelManager'
