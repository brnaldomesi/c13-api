import enum
import msgpack
from base64 import urlsafe_b64decode, urlsafe_b64encode


DEFAULT_PAGE_LIMIT = 25


class SortOrder(enum.Enum):
    DESC: str = 'desc'
    ASC: str = 'asc'


class PageDirection(enum.Enum):
    FORWARD = enum.auto()
    BACKWARD = enum.auto()


def decode_cursor(encoded_cursor):
    return msgpack.unpackb(urlsafe_b64decode(encoded_cursor), raw=False)


def encode_cursor(item, fields):
    payload = { key: item[key] for key in fields }
    packed = msgpack.packb(payload, use_bin_type=True)
    return urlsafe_b64encode(packed).decode('ascii')
