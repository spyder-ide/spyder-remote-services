from __future__ import annotations
from http.client import responses
from typing import Any
import traceback

from jupyter_server.auth.decorator import authorized, ws_authenticated
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.base.websocket import WebSocketMixin
import orjson
from tornado import web

from spyder_remote_services.services.fsspec.mixin import (
    FileOpenWebSocketHandler,
    FSSpecRESTMixin,
)


class ReadWriteWebsocketHandler(WebSocketMixin,
                                FileOpenWebSocketHandler,
                                JupyterHandler):
    auth_resource = "spyder-services"

    @ws_authenticated
    async def get(self, *args, **kwargs):
        """Handle the initial websocket upgrade GET request."""
        await super().get(*args, **kwargs)


class BaseFSSpecHandler(FSSpecRESTMixin, JupyterHandler):
    auth_resource = "spyder-services"

    def write_json(self, data, status=200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(orjson.dumps(data))

    def write_error(self, status_code, **kwargs):
        """APIHandler errors are JSON, not human pages."""
        self.set_header("Content-Type", "application/json")
        reason = responses.get(status_code, "Unknown HTTP Error")
        reply: dict[str, Any] = {
            "message": reason,
        }
        exc_info = kwargs.get("exc_info")
        if exc_info:
            e = exc_info[1]
            if isinstance(e, web.HTTPError):
                reply["message"] = e.log_message or reason
                reply["reason"] = e.reason
            else:
                reply["type"] = type(e).__name__
                reply["message"] = str(e)
                reply["traceback"] = traceback.format_exception(*exc_info)
        self.log.warning("wrote error: %r", reply["message"], exc_info=True)
        self.finish(orjson.dumps(reply))

class LsHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def get(self, path):
        detail_arg = self.get_argument("detail", default="true").lower()
        detail = detail_arg == "true"
        result = self.fs_ls(path, detail=detail)
        self.write_json(result)


class InfoHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def get(self, path):
        result = self.fs_info(path)
        self.write_json(result)



class ExistsHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def get(self, path):
        result = self.fs_exists(path)
        self.write_json({"exists": result})


class IsFileHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def get(self, path):
        result = self.fs_isfile(path)
        self.write_json({"isfile": result})


class IsDirHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def get(self, path):
        result = self.fs_isdir(path)
        self.write_json({"isdir": result})


class MkdirHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def post(self, path):
        create_parents = (self.get_argument("create_parents", "true").lower() == "true")
        exist_ok = (self.get_argument("exist_ok", "false").lower() == "true")
        result = self.fs_mkdir(path, create_parents=create_parents, exist_ok=exist_ok)
        self.write_json(result)


class RmdirHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def delete(self, path):
        result = self.fs_rmdir(path)
        self.write_json(result)


class RemoveFileHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def delete(self, path):
        missing_ok = (self.get_argument("missing_ok", "false").lower() == "true")
        result = self.fs_rm_file(path, missing_ok=missing_ok)
        self.write_json(result)


class TouchHandler(BaseFSSpecHandler):
    @web.authenticated
    @authorized
    def post(self, path):
        truncate = (self.get_argument("truncate", "true").lower() == "true")
        result = self.fs_touch(path, truncate=truncate)
        self.write_json(result)


_path_regex = r"file://(?P<path>.+)"

handlers = [
    (rf"/fsspec/open/{_path_regex}", ReadWriteWebsocketHandler),  # WebSocket
    (rf"/fsspec/ls/{_path_regex}", LsHandler),                  # GET
    (rf"/fsspec/info/{_path_regex}", InfoHandler),              # GET
    (rf"/fsspec/exists/{_path_regex}", ExistsHandler),          # GET
    (rf"/fsspec/isfile/{_path_regex}", IsFileHandler),          # GET
    (rf"/fsspec/isdir/{_path_regex}", IsDirHandler),            # GET
    (rf"/fsspec/mkdir/{_path_regex}", MkdirHandler),            # POST
    (rf"/fsspec/rmdir/{_path_regex}", RmdirHandler),            # DELETE
    (rf"/fsspec/file/{_path_regex}", RemoveFileHandler),        # DELETE
    (rf"/fsspec/touch/{_path_regex}", TouchHandler),            # POST
]
