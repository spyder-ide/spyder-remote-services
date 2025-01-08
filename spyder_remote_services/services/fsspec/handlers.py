import logging

import orjson
from jupyter_server.auth.decorator import ws_authenticated, authorized
from jupyter_server.base.handlers import JupyterHandler
from jupyter_server.base.websocket import WebSocketMixin
from tornado import web

from spyder_remote_services.services.fsspec.mixin import (
    FileOpenWebSocketHandler,
    FSSpecRESTMixin,
)


_logger = logging.getLogger(__name__)


class ReadWriteWebsocketHandler(WebSocketMixin,
                                FileOpenWebSocketHandler,
                                JupyterHandler):
    auth_resource = "spyder-services"

    @ws_authenticated
    async def get(self, *args, **kwargs):
        """Handle the initial websocket upgrade GET request."""
        await super().get(*args, **kwargs)


class BaseFSSpecHandler(FSSpecRESTMixin, JupyterHandler):
    """
    Base class combining:
      - jupyter_server APIHandler
      - Our REST mixin with fsspec-like operations
    """

    auth_resource = "spyder-services"

    def write_json(self, data, status=200):
        self.set_status(status)
        self.set_header("Content-Type", "application/json")
        self.finish(orjson.dumps(data))


class LsHandler(BaseFSSpecHandler):
    """
    GET /fsspec/ls?path=...
    Optional: ?detail=true|false
    """

    @web.authenticated
    @authorized
    def get(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return

        detail_arg = self.get_argument("detail", default="true").lower()
        detail = detail_arg == "true"

        try:
            result = self.fs_ls(path, detail=detail)
            self.write_json(result)
        except FileNotFoundError as e:
            self.write_json({"error": str(e)}, status=404)
        except Exception as e:
            _logger.exception("Error in LsHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class InfoHandler(BaseFSSpecHandler):
    """
    GET /fsspec/info?path=...
    """

    @web.authenticated
    @authorized
    def get(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        try:
            result = self.fs_info(path)
            self.write_json(result)
        except FileNotFoundError as e:
            self.write_json({"error": str(e)}, status=404)
        except Exception as e:
            _logger.exception("Error in InfoHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class ExistsHandler(BaseFSSpecHandler):
    """
    GET /fsspec/exists?path=...
    Returns: { "exists": true/false }
    """

    @web.authenticated
    @authorized
    def get(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        try:
            result = self.fs_exists(path)
            self.write_json({"exists": result})
        except Exception as e:
            _logger.exception("Error in ExistsHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class IsFileHandler(BaseFSSpecHandler):
    """
    GET /fsspec/isfile?path=...
    Returns: { "isfile": bool }
    """

    @web.authenticated
    @authorized
    def get(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        try:
            result = self.fs_isfile(path)
            self.write_json({"isfile": result})
        except Exception as e:
            _logger.exception("Error in IsFileHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class IsDirHandler(BaseFSSpecHandler):
    """
    GET /fsspec/isdir?path=...
    Returns: { "isdir": bool }
    """

    @web.authenticated
    @authorized
    def get(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        try:
            result = self.fs_isdir(path)
            self.write_json({"isdir": result})
        except Exception as e:
            _logger.exception("Error in IsDirHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class MkdirHandler(BaseFSSpecHandler):
    """
    POST /fsspec/mkdir?path=...
    Optional: ?create_parents=true/false
              ?exist_ok=false/true
    """

    @web.authenticated
    @authorized
    def post(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        create_parents = (self.get_argument("create_parents", "true").lower() == "true")
        exist_ok = (self.get_argument("exist_ok", "false").lower() == "true")

        try:
            result = self.fs_mkdir(path, create_parents=create_parents, exist_ok=exist_ok)
            self.write_json(result)
        except Exception as e:
            _logger.exception("Error in MkdirHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class RmdirHandler(BaseFSSpecHandler):
    """
    DELETE /fsspec/rmdir?path=...
    Removes directory if empty
    """

    @web.authenticated
    @authorized
    def delete(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        try:
            result = self.fs_rmdir(path)
            self.write_json(result)
        except FileNotFoundError as e:
            self.write_json({"error": str(e)}, status=404)
        except OSError as e:
            # e.g. OSError if directory not empty
            self.write_json({"error": str(e)}, status=400)
        except Exception as e:
            _logger.exception("Error in RmdirHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class RemoveFileHandler(BaseFSSpecHandler):
    """
    DELETE /fsspec/file?path=...
    Optional: ?missing_ok=true/false
    """

    @web.authenticated
    @authorized
    def delete(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        missing_ok = (self.get_argument("missing_ok", "false").lower() == "true")
        try:
            result = self.fs_rm_file(path, missing_ok=missing_ok)
            self.write_json(result)
        except Exception as e:
            _logger.exception("Error in RemoveFileHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


class TouchHandler(BaseFSSpecHandler):
    """
    POST /fsspec/touch?path=...
    Optional: ?truncate=true/false
    """

    @web.authenticated
    @authorized
    def post(self, path):
        if not path:
            self.write_json({"error": "Missing 'path' parameter"}, status=400)
            return
        truncate = (self.get_argument("truncate", "true").lower() == "true")

        try:
            result = self.fs_touch(path, truncate=truncate)
            self.write_json(result)
        except Exception as e:
            _logger.exception("Error in TouchHandler for path=%s", path)
            self.write_json({"error": str(e)}, status=500)


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
