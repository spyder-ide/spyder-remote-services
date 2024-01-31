from spyder_remote_server.services.kernel_manager.handlers import KernelHandler

ROUTES = [
    (r'/services/spyder-service/kernel/?(?P<session_key>[^\/]+)?', KernelHandler)
]
