import json
import threading
import subprocess
import asyncio
import time
import sys
from pathlib import Path
import logging
import atexit


_logger = logging.getLogger(__name__)

class KernelProcess:
    command = [sys.executable, "-m", "spyder_kernels.console"]

    def __init__(self):
        self._process = None

    def start(self):
        self._process = subprocess.Popen(self.command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def terminate(self):
        if self._process is not None:
            self._process.terminate()
    
    def kill(self):
        if self._process is not None:
            self._process.kill()

    def is_alive(self):
        if self._process is not None:
            return self._process.poll() is None
        return False
    
    def join(self):
        if self._process is not None:
            self._process.wait()
    
    @property
    def pid(self):
        if self._process is None:
            return None
        return self._process.pid


class KernelManager:
    _instance = None
    __rlock = threading.RLock()
    __inside_instance = False

    @classmethod
    def instance(cls: type['KernelManager'], *args: list, **kwargs: dict) -> 'KernelManager':
        """Get *the* class instance.

        Return the instance of the class. If it did not exist yet, create it
        by calling the "constructor" with whatever arguments and keyword arguments
        provided.

        Returns:
            instance(object): Class Singleton Instance
        """
        if cls._instance is not None:
            return cls._instance
        with cls.__rlock:
            # Re-check, perhaps it was created in the meantime...
            if cls._instance is None:
                cls.__inside_instance = True
                try:
                    cls._instance = cls(*args, **kwargs)
                finally:
                    cls.__inside_instance = False
        return cls._instance

    def __new__(cls: type['KernelManager'], *args: list, **kwargs: dict) -> 'KernelManager':
        """Class constructor.

        Ensures that this class isn't created without the ``instance`` class method.

        Raises:
            RuntimeError: Exception when not called from the ``instance`` class method.

        Returns:
            object: Class instance.
        """
        if cls._instance is None:
            with cls.__rlock:
                if cls._instance is None and cls.__inside_instance:
                    return super().__new__(cls, *args, **kwargs)

        msg = f'Attempt to create a {cls.__qualname__} instance outside of instance()'
        raise RuntimeError(
            msg,
        )

    def __init__(self):
        self.kernels = {}
        atexit.register(self.__del__)

    def __del__(self):
        for process in self.kernels.values():
            process.terminate()
            process.join()

    async def start_kernel(self):
        # Logic to start a kernel and return connection info
        process = KernelProcess()
        process.start()

        connection_file = self._get_jupyter_runtime_dir() / f"kernel-{process.pid}.json"

        # wait until file is created for 5 seconds
        start_time = time.time()
        while not connection_file.exists():
            if time.time() - start_time > 4:
                if process.is_alive():
                    process.kill()
                raise RuntimeError("Kernel did not start in time, unknown error")
            await asyncio.sleep(0.1)

        with open(connection_file, 'r') as f:
            result = json.load(f)

        self.kernels[result['key']] = process

        return result

    @staticmethod
    def _get_jupyter_runtime_dir():
        return Path(subprocess.check_output(['jupyter', '--runtime-dir']).decode('utf-8').strip())

    async def stop_kernel(self, session_key):
        process = self.kernels.pop(session_key)
        process.terminate()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, process.join)
        return not process.is_alive()

    def check_kernel_alive(self, session_key):
        process = self.kernels[session_key]
        return process.is_alive()

    def get_kernel_pid(self, session_key):
        process = self.kernels[session_key]
        return process.pid

    def list_kernels(self):
        return list(self.kernels.keys())
