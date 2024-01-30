import json
from functools import wraps

import dataclasses
import pickle


@dataclasses.dataclass
class Status:
    SUCCESS = 200
    ERROR = 500


@dataclasses.dataclass
class Response:
    status: int
    value: object = None
    exception: Exception = None

    def to_bytes(self):
        return pickle.dumps(self)

    @classmethod
    def from_bytes(cls, data):
        return pickle.loads(data)


@dataclasses.dataclass
class Request:
    data: object = None

    def to_bytes(self):
        return pickle.dumps(self)

    @classmethod
    def from_bytes(cls, data):
        return pickle.loads(data)


def handle_post(func):
    @wraps(func)
    async def wrapper(handler):
        try:
            data = json.loads(handler.request.body)
            value = await func(handler, data)
        except Exception as e:
            response = Response(Status.ERROR, exception=e)
        else:
            response = Response(Status.SUCCESS, value=value)

        handler.write(response.to_bytes())

    return wrapper
