import tornado

from spyder_remote_server.app.kernel_manager.core import KernelManager


class KernelHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.kernel_manager = KernelManager.instance()

    async def post(self, session_key=None):
        connection_info = await self.kernel_manager.start_kernel()
        self.write(connection_info)
    
    async def delete(self, session_key=None):
        success = await self.kernel_manager.stop_kernel(session_key)
        self.write({'success': success})

    async def get(self, session_key=None):
        if session_key is None:
            kernels_keys = self.kernel_manager.list_kernels()
            self.write({'kernels': kernels_keys})
        else:
            alive = self.kernel_manager.check_kernel_alive(session_key)
            pid = self.kernel_manager.get_kernel_pid(session_key)
            self.write({'alive': alive, 'pid': pid})
