from spyder_remote_server.app.kernel_manager.handlers import KernelHandler

ROUTES = [
    (r'/services/spyder-service/kernel/?(?P<session_key>[^\/]+)?', KernelHandler)
]
