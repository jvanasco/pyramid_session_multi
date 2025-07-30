# stdlib
import datetime
import json
import re
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

# pyramid

# ==============================================================================


RE_value_datetime_1 = re.compile(
    r"^__datetime__\|(\d){4}-(\d){2}-(\d){2}T(\d){2}:(\d){2}:(\d){2}$"
)


class JsonEncoder_Datetime(json.JSONEncoder):
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


def decoder_pair_hook(payload: List[Tuple[Any, Any]]) -> Dict:
    """custom decoding of data strutures."""
    rval: Dict = {}
    for k, v in payload:
        rval[k] = v
        if isinstance(v, str):
            if RE_value_datetime_1.match(v):
                rval[k] = datetime.datetime.strptime(
                    v.split("|")[1], "%Y-%m-%dT%H:%M:%S"
                )
    return rval


def py2json(payload: Any) -> str:
    return json.dumps(
        payload, cls=JsonEncoder_Datetime, separators=(",", ":"), sort_keys=True
    )


def json2py(payload: str) -> Any:
    return json.loads(payload, object_pairs_hook=decoder_pair_hook)


class JSONSerializerWithDatetime(object):

    def dumps(self, appstruct: Any) -> bytes:
        """
        Accept a Python object and return bytes.
        """
        return py2json(appstruct).encode()

    def loads(self, bstruct: Union[bytes, str]) -> Any:
        """Accept bytes and return a Python object."""
        if isinstance(bstruct, bytes):
            return json2py(bstruct.decode())
        return json2py(bstruct)
