from jupyter_client.ioloop import AsyncIOLoopKernelManager


class SpyderAsyncIOLoopKernelManager(AsyncIOLoopKernelManager):
    def format_kernel_cmd(self, extra_arguments=None):
        """Format the kernel command line to be run."""
        cmd = super().format_kernel_cmd(extra_arguments)
        # Replace the `ipykernel_launcher` with `spyder_kernel.console`
        cmd_indx = cmd.index('ipykernel_launcher')
        if cmd_indx != -1:
            cmd[cmd_indx] = 'spyder_kernels.console'
        return cmd

