"""
This is not a test file, but used to determine performance between serializers
"""

# stdlib
import datetime
import json
import re
import timeit
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

# pypi
from typing_extensions import TypedDict

# ==============================================================================

#
# Encoder 1
#
# Datetime is encoded into an ISO 8601 compatible string
#
DATETIME_1__RE = re.compile(
    r"^__datetime__\|(\d){4}-(\d){2}-(\d){2}T(\d){2}:(\d){2}:(\d){2}$"
)


class DATETIME_1__JsonEncoder(json.JSONEncoder):
    """Extends JSONEncoder for datetime type."""

    def encode_datetime(self, dt: datetime.datetime) -> str:
        """Serialize the given datetime.datetime object to a JSON string."""
        # Default is ISO 8601 compatible (standard notation).
        # Don't use strftime because that can't handle dates before 1900.
        return "__datetime__|%04d-%02d-%02dT%02d:%02d:%02d" % (
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
        )

    def default(self, o: Any):
        # We MUST check for a datetime.datetime instance before datetime.date.
        # datetime.datetime is a subclass of datetime.date, and therefore
        # instances of it are also instances of datetime.date.
        if isinstance(o, datetime.datetime):
            return self.encode_datetime(o)
        else:
            return json.JSONEncoder.default(self, o)


def DATETIME_1__JsonDecoder(payload: List[Tuple[Any, Any]]) -> Dict:
    """custom decoding of data strutures."""
    rval: Dict = {}
    for k, v in payload:
        rval[k] = v
        if isinstance(v, str):
            if DATETIME_1__RE.match(v):
                rval[k] = datetime.datetime.strptime(
                    v.split("|")[1], "%Y-%m-%dT%H:%M:%S"
                )
    return rval


def DATETIME_1__py2json(payload: Any) -> str:
    return json.dumps(
        payload, cls=DATETIME_1__JsonEncoder, separators=(",", ":"), sort_keys=True
    )


def DATETIME_1__json2py(payload: str) -> Any:
    return json.loads(payload, object_pairs_hook=DATETIME_1__JsonDecoder)


class DATETIME_1__JSONSerializer(object):

    def dumps(self, appstruct: Any) -> bytes:
        """
        Accept a Python object and return bytes.
        """
        return DATETIME_1__py2json(appstruct).encode()

    def loads(self, bstruct: Union[bytes, str]) -> Any:
        """Accept bytes and return a Python object."""
        if isinstance(bstruct, bytes):
            return DATETIME_1__json2py(bstruct.decode())
        return DATETIME_1__json2py(bstruct)


#
# Encoder 2
#
# Datetime is encoded into an Epoch
#
DATETIME_2__RE = re.compile(r"^__datetime__\|(\d+)$")


class DATETIME_2__JsonEncoder(json.JSONEncoder):
    """Extends JSONEncoder for datetime type."""

    def encode_datetime(self, dt: datetime.datetime) -> str:
        """Serialize the given datetime.datetime object to a JSON string."""
        # Default is ISO 8601 compatible (standard notation).
        return "__datetime__|%d" % dt.timestamp()

    def default(self, o: Any):
        # We MUST check for a datetime.datetime instance before datetime.date.
        # datetime.datetime is a subclass of datetime.date, and therefore
        # instances of it are also instances of datetime.date.
        if isinstance(o, datetime.datetime):
            return self.encode_datetime(o)
        else:
            return json.JSONEncoder.default(self, o)


def DATETIME_2__JsonDecoder(payload: List[Tuple[Any, Any]]) -> Dict:
    """custom decoding of data strutures."""
    rval: Dict = {}
    for k, v in payload:
        rval[k] = v
        if isinstance(v, str):
            if DATETIME_2__RE.match(v):
                rval[k] = datetime.datetime.fromtimestamp(int(v.split("|")[1]))
    return rval


def DATETIME_2__py2json(payload: Any) -> str:
    return json.dumps(
        payload, cls=DATETIME_2__JsonEncoder, separators=(",", ":"), sort_keys=True
    )


def DATETIME_2__json2py(payload: str) -> Any:
    return json.loads(payload, object_pairs_hook=DATETIME_2__JsonDecoder)


class DATETIME_2__JSONSerializer(object):

    def dumps(self, appstruct: Any) -> bytes:
        """
        Accept a Python object and return bytes.
        """
        return DATETIME_2__py2json(appstruct).encode()

    def loads(self, bstruct: Union[bytes, str]) -> Any:
        """Accept bytes and return a Python object."""
        if isinstance(bstruct, bytes):
            return DATETIME_1__json2py(bstruct.decode())
        return DATETIME_1__json2py(bstruct)


#
# Run the tests
#
class TYPE_ENCODABLE(TypedDict):
    version: int
    name: str
    datetime: datetime.datetime


_DATETIME_1__JSONSerializer = DATETIME_1__JSONSerializer()
_DATETIME_2__JSONSerializer = DATETIME_2__JSONSerializer()


def DATETIME_1_RoundTrip(audit: bool = False):
    payload: TYPE_ENCODABLE = {
        "version": 1,
        "name": "DATETIME_1",
        "datetime": datetime.datetime.utcnow(),
    }
    _encoded = _DATETIME_1__JSONSerializer.dumps(payload)
    _decoded = _DATETIME_1__JSONSerializer.loads(_encoded)
    if audit:
        assert payload["datetime"].replace(microsecond=0) == _decoded["datetime"]


def DATETIME_2_RoundTrip(audit: bool = False):
    payload: TYPE_ENCODABLE = {
        "version": 1,
        "name": "DATETIME_2",
        "datetime": datetime.datetime.utcnow(),
    }
    _encoded = _DATETIME_2__JSONSerializer.dumps(payload)
    _decoded = _DATETIME_2__JSONSerializer.loads(_encoded)
    if audit:
        assert payload["datetime"].replace(microsecond=0) == _decoded["datetime"]


DATETIME_1_RoundTrip(audit=True)
DATETIME_2_RoundTrip(audit=True)

execution_time_1 = timeit.timeit(stmt=DATETIME_1_RoundTrip, number=10000)
execution_time_2 = timeit.timeit(stmt=DATETIME_2_RoundTrip, number=10000)

print(execution_time_1)
print(execution_time_2)
