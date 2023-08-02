from abc import ABC, abstractmethod
from datetime import *
from enum import Enum
from typing import Dict, Union, List

from submitscript.util.deserialization_error import DeserializationError


class SerializableData(ABC):

    @classmethod
    @abstractmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'SerializableData':
        pass

    @abstractmethod
    def serialize(self) -> Union[Dict, List]:
        pass

    @classmethod
    def require_type(cls, obj: Union[Dict, List], required_type: type):
        if not isinstance(obj, required_type):
            raise DeserializationError("Could not deserialize %s: Not a %s" % (cls.__name__, required_type.__name__))

    @classmethod
    def deserialize(cls, obj: Union[Dict, List]):
        try:
            return cls.deserialize_impl(obj)
        except DeserializationError:
            raise
        except Exception as e:
            raise DeserializationError("Could not deserialize %s: %s" % (cls.__name__, str(e)))


def deserialize_enum(enum_class: type, obj: str):
    """
    Helper function to deserialize enums. Unfortunately is does not appear to be possible to extend both Enum and ABC (by proxy via SerializableData).
    To unify the serialization and deserialization this function and :func`~serialize_enum` exist.
    :param enum_class: The class of the enum that shall be deserialized.
    :param obj: The object to deserialize into an enum_class object
    :return: The deserialized object
    """
    if not isinstance(obj, str):
        raise DeserializationError("Could not deserialize %s: Not a %s" % (enum_class.__name__, str.__name__))

    try:
        return enum_class(obj)
    except Exception as e:
        raise DeserializationError("Could not deserialize %s: %s." % (enum_class.__name__, str(e)))


def serialize_enum(obj: Enum):
    """
    Helper function to serialize enums.
    While trivial, this exists to complement :func`~deserialize_enum`
    :param obj:
    :return:
    """
    return obj.value


def serialize(obj):
    """JSON serializer for objects not serializable by default."""

    if isinstance(obj, date):
        return obj.isoformat()

    if isinstance(obj, time):
        return obj.isoformat()

    if isinstance(obj, Enum):
        return str(obj.value)

    return obj.__dict__
