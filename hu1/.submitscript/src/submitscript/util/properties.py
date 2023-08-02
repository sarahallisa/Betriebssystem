import json
from abc import abstractmethod, ABC
from pathlib import Path
from typing import Optional, Generic, TypeVar, Type

from submitscript.output import global_log_file
from submitscript.util.map_optional import map_optional
from submitscript.util.serialize import SerializableData

T = TypeVar("T")
T2 = TypeVar("T2", bound=SerializableData)


class Property(Generic[T], ABC):
    @abstractmethod
    def get(self) -> Optional[T]:
        pass

    @abstractmethod
    def set(self, value: Optional[T]) -> None:
        pass

    @abstractmethod
    def has_value(self) -> bool:
        pass

    def json_serialized(self, serialized_type: Optional[Type[T2]] = None) -> 'JsonProperty[T2]':
        return JsonProperty(serialized_type, self)

    def cached(self) -> 'CachedProperty[T]':
        return CachedProperty(self)


class TextFileProperty(Property[str]):
    def __init__(self, path: Path):
        self.path = path

    def get(self) -> Optional[str]:
        if not self.path.is_file():
            return None

        with open(self.path, "r") as f:
            return f.read()

    def set(self, value: Optional[str]) -> None:
        if value is None:
            if self.path.exists():
                self.path.unlink()
        else:
            with open(self.path, "w") as f:
                f.write(value)
                f.write("\n")

            if not self.path.exists():
                global_log_file.error("Assertion error! Property file '%s' does not exist after it should have been created." % str(self.path))

    def has_value(self) -> bool:
        return self.path.exists()


class JsonProperty(Property[T]):
    def __init__(self, serialized_type: Optional[Type[T2]], base_property: Property[str]):
        self.base_property = base_property
        self.serialized_type = serialized_type

    def has_value(self) -> bool:
        return self.base_property.has_value()

    def get(self) -> Optional[T]:
        base_value = self.base_property.get()

        if base_value is None:
            return None
        else:
            loaded = json.loads(base_value)

            return loaded if self.serialized_type is None else self.serialized_type.deserialize(loaded)

    def set(self, value: Optional[T]) -> None:
        self.base_property.set(map_optional(value, lambda v: json.dumps(v.serialize() if self.serialized_type is not None else v, indent=4, sort_keys=True)))


class CachedProperty(Property[T]):
    def __init__(self, base_property: Property[T]):
        self.base_property = base_property

        # The cached value
        self.value: Optional[T] = None

    def has_value(self) -> bool:
        return self.value is not None or self.base_property.has_value()

    def get(self) -> Optional[T]:
        if self.value is None:
            self.value = self.base_property.get()

        return self.value

    def set(self, value: Optional[T]) -> None:
        self.base_property.set(value)
        self.value = value
