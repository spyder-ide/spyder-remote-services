from __future__ import annotations
import asyncio
import base64
import datetime
from http import HTTPStatus
import logging
import os
from pathlib import Path
import stat
import sys
import threading
import time
import traceback

import orjson
from tornado.websocket import WebSocketHandler


_logger = logging.getLogger(__name__)


class FileOpenWebSocketHandler(WebSocketHandler):
    """
    WebSocket handler for opening files and streaming data.

    The protocol on message receive (JSON messages):
      {
        "method": "read", # "write", "seek", etc.  (required)
        "kwargs": {...},  (optional)
        "data": "<base64-encoded chunk>",  # all data is base64-encoded  (optional)
      }

    The protocol for sending data back to the client:
      {
        "status": 200,  # HTTP status code  (required)
        "data": "<base64-encoded chunk>",  # response data if any  (optional)
        "error": {"message": "error message",  (required)
                  "traceback": ["line1", "line2", ...]  (optional)}  # if an error occurred  (optional)
      }
    """

    LOCK_TIMEOUT = 100  # seconds

    max_message_size = 5 * 1024 * 1024 * 1024  # 5 GB

    __thread_lock = threading.Lock()

    # ----------------------------------------------------------------
    # Tornado WebSocket / Handler Hooks
    # ----------------------------------------------------------------
    async def open(self, path,
                   mode="r", lock=None, atomic=False):
        """Open file."""
        self.path = self._load_path(path)
        self.atomic = atomic

        if lock and not await self._acquire_lock(path):
            self.close(1002, "Failed to acquire lock.")
            return

        if self.atomic:
            self.file = self.atomic_path.open(mode)
        else:
            self.file = self.path.open(mode)

    async def on_close(self):
        """Close file."""
        self.file.close()
        if self.atomic:
            self.atomic_path.replace(self.path)
        if self.__locked:
            self._release_lock()

    async def on_message(self, raw_message):
        """Handle incoming messages."""
        try:
            await self.handle_message(raw_message)
        except Exception as e:
            _logger.exception("Error handling message")
            await self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR,
                                   f"Error handling message {e}",
                                   exec_info=e)

    async def handle_message(self, raw_message):
        """Handle incoming JSON messages (read/write commands only)."""
        msg = await self._decode_json(raw_message)
        if not msg:
            return

        method = msg.get("method")
        kwargs = msg.get("kwargs", {})
        data = msg.get("data")

        if not method:
            await self._send_error(HTTPStatus.BAD_REQUEST,
                                   "No 'method' provided.")
            return

        # Lookup
        func = getattr(self, f"_handle_{method}", None)
        if func is None:
            await self._send_error(
                HTTPStatus.NOT_FOUND,
                f"Unknown or unsupported method: {method}"
                )
            return

        if data:
            kwargs["data"] = base64.b64decode(data)

        try:
            value = await func(**kwargs)
        except Exception as e:
            _logger.exception("Error in method '%s':", method)
            await self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Error in method '{method}': {e}",
                exec_info=e,
            )

        await self._send_json(status=HTTPStatus.OK, value=value)

    # ----------------------------------------------------------------
    # Internal Helpers
    # ----------------------------------------------------------------
    async def _acquire_lock(self, __start_time=None):
        """Acquire a lock on the file."""
        if __start_time is None:
            __start_time = time.time()

        while self.__locked:
            await asyncio.sleep(1)
            if time.time() - __start_time > self.LOCK_TIMEOUT:
                return False

        with self.__thread_lock:
            if self.__locked:
                return await self._acquire_lock(__start_time=__start_time)
            self.lock_path.touch(exist_ok=False)

        return True

    def _release_lock(self):
        """Release the lock on the file."""
        with self.__thread_lock:
            self.lock_path.unlink(missing_ok=True)

    @property
    def atomic_path(self):
        """Get the path to the atomic file."""
        return self.path.parent / f".{self.path.name}.spyder.tmp"

    @property
    def lock_path(self):
        """Get the path to the atomic file."""
        return self.path.parent / f".{self.path.name}.spyder.lck"

    @property
    def __locked(self):
        return Path(self.lock_path).exists()

    async def _decode_json(self, raw_message):
        """Decode a JSON message (non-streamed)."""
        try:
            return orjson.loads(raw_message)
        except orjson.JSONDecodeError:
            _logger.exception("Invalid JSON: %s", raw_message)
            await self._send_error(HTTPStatus.BAD_REQUEST,
                                   f"Invalid JSON: {raw_message}")
            return None

    async def _send_json(self, status: HTTPStatus, data: dict):
        """Send a single JSON message."""
        await self.write_message(orjson.dumps(
            {"status": status.value, **data}
        ))

    async def _send_error(self,
                          status: HTTPStatus,
                          error_msg: str,
                          exec_info: bool |
                                     BaseException |
                                     tuple |
                                     None = None):
        """Send an error response to the client."""
        data = {"message": error_msg}
        if exec_info:
            if isinstance(exec_info, BaseException):
                data["traceback"] = traceback.format_exception(
                    type(exec_info), exec_info, exec_info.__traceback__)
            elif isinstance(exec_info, tuple):
                data["traceback"] = traceback.format_exception(*exec_info)
            else:
                data["traceback"] = traceback.format_exception(*sys.exc_info())
        await self._send_json(status=status, data={"error": data})

    def _load_path(self, path_str: str) -> Path:
        """Convert path string to a Path object."""
        return Path(path_str)

    # ----------------------------------------------------------------
    # Write Operation
    # ----------------------------------------------------------------
    async def _handle_write(self, data: bytes | str) -> int:
        """Write data to the file."""
        return self.file.write(data)

    async def _handle_flush(self):
        """Flush the file."""
        return self.file.flush()

    async def _handle_read(self, n: int = -1) -> bytes | str:
        """Read data from the file."""
        return self.file.read(n)

    async def _handle_seek(self, offset: int, whence: int = 0) -> int:
        """Seek to a new position in the file."""
        return self.file.seek(offset, whence)

    async def _handle_tell(self) -> int:
        """Get the current file position."""
        return self.file.tell()

    async def _handle_truncate(self, size: int | None = None) -> int:
        """Truncate the file to a new size."""
        return self.file.truncate(size)


class FSSpecRESTMixin:
    """
    REST handler for fsspec-like filesystem operations, using pathlib.Path.

    Supports:
        - fs_ls(path_str, detail=True)
        - fs_info(path_str)
        - fs_exists(path_str)
        - fs_isfile(path_str)
        - fs_isdir(path_str)
        - fs_mkdir(path_str, create_parents=True, exist_ok=False)
        - fs_rmdir(path_str)
        - fs_rm_file(path_str, missing_ok=False)
        - fs_touch(path_str, truncate=True)
    """

    def _info_for_path(self, path: Path) -> dict:
        """Get fsspec-like info about a single path."""
        out = path.stat(follow_symlinks=False)
        link = stat.S_ISLNK(out.st_mode)
        if link:
            # If it's a link, stat the target
            out = path.stat(follow_symlinks=True)
        size = out.st_size
        if stat.S_ISDIR(out.st_mode):
            t = "directory"
        elif stat.S_ISREG(out.st_mode):
            t = "file"
        else:
            t = "other"
        result = {
            "name": str(path),
            "size": size,
            "type": t,
            "created": out.st_ctime,
            "islink": link,
        }
        for field in ["mode", "uid", "gid", "mtime", "ino", "nlink"]:
            result[field] = getattr(out, f"st_{field}", None)
        if link:
            result["destination"] = str(path.resolve())

        return result

    def _load_path(self, path_str: str) -> Path | None:
        """Convert a path string to a pathlib.Path object safely."""
        try:
            return Path(path_str)
        except Exception as e:
            _logger.exception("Failed to load path: %s", path_str)
            raise e  # Up to the handler to convert to HTTP error.

    def fs_ls(self, path_str: str, detail: bool = True):
        """List objects at path, like fsspec.ls()."""
        path = self._load_path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        if path.is_file():
            # fsspec.ls of a file often returns a single entry
            if detail:
                return [self._info_for_path(path)]
            else:
                return [str(path)]

        # Otherwise, it's a directory
        results = []
        for p in path.iterdir():
            if detail:
                results.append(self._info_for_path(p))
            else:
                results.append(str(p))
        return results

    def fs_info(self, path_str: str):
        """Get info about a single path, like fsspec.info()."""
        path = self._load_path(path_str)
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        return self._info_for_path(path)

    def fs_exists(self, path_str: str) -> bool:
        """Like fsspec.exists()."""
        path = self._load_path(path_str)
        return path.exists()

    def fs_isfile(self, path_str: str) -> bool:
        """Like fsspec.isfile()."""
        path = self._load_path(path_str)
        return path.is_file()

    def fs_isdir(self, path_str: str) -> bool:
        """Like fsspec.isdir()."""
        path = self._load_path(path_str)
        return path.is_dir()

    def fs_mkdir(self, path_str: str, create_parents: bool = True, exist_ok: bool = False):
        """Like fsspec.mkdir()."""
        path = self._load_path(path_str)
        path.mkdir(parents=create_parents, exist_ok=exist_ok)
        return {"success": True}

    def fs_rmdir(self, path_str: str):
        """Like fsspec.rmdir() - remove if empty."""
        path = self._load_path(path_str)
        path.rmdir()
        return {"success": True}

    def fs_rm_file(self, path_str: str, missing_ok: bool = False):
        """Like fsspec.rm_file(), remove a single file."""
        path = self._load_path(path_str)
        path.unlink(missing_ok=missing_ok)
        return {"success": True}

    def fs_touch(self, path_str: str, truncate: bool = True):
        """
        Like fsspec.touch(path, truncate=True).
        If truncate=True, zero out file if exists. Otherwise just update mtime.
        """
        path = self._load_path(path_str)
        if path.exists() and not truncate:
            now = datetime.datetime.now().timestamp()
            os.utime(path, (now, now))
        else:
            # create or overwrite
            with path.open("wb"):
                pass
        return {"success": True}
