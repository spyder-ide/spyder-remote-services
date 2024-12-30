from __future__ import annotations
import base64
import datetime
import logging
import os
from pathlib import Path
import stat
import traceback

import orjson


CHUNK_SIZE = 2**20  # 1 MB per chunk, adjust as needed
_logger = logging.getLogger(__name__)


class FSSpecWebSocketMixin:
    """
    WebSocket handler for *only* read/write file operations in a chunked,
    fsspec-like manner.

    Supports:
      - cat_file(start=None, end=None)
      - read_block(offset, length, delimiter=None)
      - write_file() in streamed chunks (client sends many base64-encoded "data" messages).

    The protocol on the wire (JSON messages):
      {
        "method": "cat_file",   # or "read_block", "write_file"
        "args": [...],
        "kwargs": {...}
      }

    For reading, the server will respond with multiple JSON messages:
      {
        "type": "data",
        "data": "<base64-encoded chunk>"
      }
      ...
      {
        "type": "eof"
      }

    For writing, the client sends multiple "data" messages to the server,
    then "eof" to finalize.
    """

    # ----------------------------------------------------------------
    # Tornado WebSocket / Handler Hooks
    # ----------------------------------------------------------------
    async def on_message(self, raw_message):
        """Handle incoming JSON messages (read/write commands only)."""
        msg = await self._decode_json(raw_message)
        if not msg:
            return

        method = msg.get("method")
        args = msg.get("args", [])
        kwargs = msg.get("kwargs", {})

        if not method:
            await self._send_error("No 'method' provided.")
            return

        # Lookup
        func = getattr(self, f"_handle_{method}", None)
        if func is None:
            await self._send_error(f"Unknown or unsupported method: {method}")
            return

        try:
            await func(*args, **kwargs)
        except Exception as e:
            _logger.exception("Error in method '%s':", method)
            await self._send_error(
                f"Error in method '{method}': {e}",
                traceback=traceback.format_exception(type(e), e, e.__traceback__),
            )

    # ----------------------------------------------------------------
    # Internal Helpers
    # ----------------------------------------------------------------
    async def _decode_json(self, raw_message):
        """Decode a JSON message (non-streamed)."""
        try:
            return orjson.loads(raw_message)
        except orjson.JSONDecodeError:
            _logger.exception("Invalid JSON: %s", raw_message)
            await self._send_error(f"Invalid JSON: {raw_message}")
            return None

    async def _send_json(self, data: dict):
        """Send a single JSON message."""
        await self.write_message(orjson.dumps(data))

    async def _send_error(self, error_msg: str, traceback: list[str] | None = None):
        """Send an error response to the client."""
        data = {"error": error_msg}
        if traceback:
            data["traceback"] = traceback
        await self._send_json(data)

    async def _send_stream_chunk(self, chunk: bytes):
        """Send a chunk of bytes as a base64-encoded message."""
        encoded = base64.b64encode(chunk).decode()
        await self._send_json({"type": "data", "data": encoded})

    async def _send_stream_eof(self):
        """Signal the end of a data stream."""
        await self._send_json({"type": "eof"})

    def _load_path(self, path_str: str) -> Path:
        """Convert path string to a Path object."""
        return Path(path_str)

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def _handle_cat_file(self, path, start=None, end=None, **kwargs):
        """
        Read the entire file (or partial range) in base64 chunks.

        Equivalent to fsspec cat_file(path, start, end).
        """
        path_obj = self._load_path(path)
        if not path_obj.exists() or not path_obj.is_file():
            await self._send_error(f"File not found or not a file: {path}")
            return

        size = path_obj.stat().st_size
        start = max(0, start if start else 0)
        end = min(size, end if end is not None else size)

        await self._stream_file(path_obj, start, end)

    async def _handle_read_block(self, fn, offset, length, delimiter=None):
        """
        Like fsspec read_block(fn, offset, length, delimiter).

        Read partial bytes from the file, possibly adjusted to the next delimiter boundary.
        """
        path = self._load_path(fn)
        if not path.exists() or not path.is_file():
            await self._send_error(f"File not found or not a file: {fn}")
            return

        size = path.stat().st_size
        offset = max(0, offset)
        end = size if length is None else min(size, offset + length)

        # If a delimiter is given, read until found
        if delimiter is not None:
            with path.open("rb") as f:
                f.seek(offset)
                chunk = f.read((end - offset) + 65536)  # read a bit extra
            idx = chunk.find(delimiter, -65536)
            if idx != -1:
                # include up through the delimiter
                end = offset + idx + len(delimiter)

        await self._stream_file(path, offset, end)

    async def _stream_file(self, path: Path, start: int, end: int):
        """Read [start:end] from `path` in chunked fashion and send to client."""
        if end < start:
            await self._send_error(f"Invalid range: start={start} > end={end}")
            return

        with path.open("rb") as f:
            f.seek(start)
            remaining = end - start
            while remaining > 0:
                to_read = min(CHUNK_SIZE, remaining)
                chunk = f.read(to_read)
                if not chunk:
                    break
                await self._send_stream_chunk(chunk)
                remaining -= len(chunk)

        await self._send_stream_eof()

    # ----------------------------------------------------------------
    # Write Operation
    # ----------------------------------------------------------------
    async def _handle_write_file(self, path):
        """
        Write a file in chunks.

        Protocol for writing:
        1) Client sends {"method": "write_file", "args": ["some/path"], "kwargs": {}}
        2) Then the client sends multiple data messages, e.g.:
           {"type": "data", "data": "<base64_chunk>"}
           ...
        3) Finally the client sends {"type": "eof"}
        4) Server writes out a response: {"type": "write_complete"} or success JSON

        open the file in 'wb' and keep appending as 'data' messages is received.
        """
        path_obj = self._load_path(path)

        f = path_obj.open("wb")

        try:
            while True:
                message = await self.read_message()
                if message is None:
                    # The client disconnected?
                    _logger.warning("Client disconnected during write_file.")
                    break

                msg = await self._decode_json(message)
                if not msg:
                    continue

                msg_type = msg.get("type")
                if msg_type == "data":
                    # Base64 decode the chunk
                    b64data = msg.get("data", "")
                    chunk = base64.b64decode(b64data)
                    f.write(chunk)
                elif msg_type == "eof":
                    # Done receiving
                    break
                else:
                    await self._send_error(
                        f"Unexpected message type during write_file: {msg_type}"
                    )
                    break

        except Exception as e:
            _logger.exception("Error while writing file: %s", path)
            await self._send_error(f"Error while writing file: {e}")
        finally:
            f.close()

        # Send final response
        await self._send_json({"type": "write_complete", "path": str(path_obj)})


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
