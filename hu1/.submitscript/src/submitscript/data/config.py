from typing import List, Union, Dict

from submitscript.util.serialize import SerializableData


class Server(SerializableData):
    def __init__(self, host: str, port: str):
        self.host = host
        self.port = port

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'Server':
        cls.require_type(obj, dict)

        return Server(obj["hostname"],
                      obj["port"])

    def serialize(self) -> Union[Dict, List]:
        return {
            "hostname": self.host,
            "port": self.port
        }

    def to_url(self):
        return "%s:%s" % (self.host, self.port)


class SkeletonVariant(SerializableData):
    def __init__(self, name: str, root: str, build: str, allowed_files: List[str], variant_data: Dict):
        self.name = name
        self.root = root
        self.build = build
        self.allowed_files = allowed_files
        self.variant_data = variant_data

    def is_filename_allowed(self, filename: str):
        for pattern in self.allowed_files:
            import fnmatch
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'SkeletonVariant':
        cls.require_type(obj, dict)

        return SkeletonVariant(
            obj["name"],
            obj["root"],
            obj["build"],
            obj["allowed_files"],
            obj.get("variant_data", {}))

    def serialize(self) -> Union[Dict, List]:
        return {
            "name": self.name,
            "root": self.root,
            "build": self.build,
            "allowed_files": self.allowed_files,
            "variant_data": self.variant_data
        }


class Config(SerializableData):
    def __init__(self, course_name: str, server: Server, max_team_size: int, assignment_names: List[str], skeleton_variants: List[SkeletonVariant]):
        self.course_name = course_name
        self.server = server
        self.max_team_size = max_team_size
        self.assignment_ids = assignment_names
        self.skeleton_variants = skeleton_variants

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'Config':
        cls.require_type(obj, dict)

        return Config(
            obj["course_name"],
            Server.deserialize(obj["server"]),
            obj["max_team_size"],
            obj["assignment_ids"],
            [SkeletonVariant.deserialize(v) for v in obj["skeleton_variants"]])

    def serialize(self) -> Union[Dict, List]:
        return {
            "course_name": self.course_name,
            "server": self.server.serialize(),
            "max_team_size": self.max_team_size,
            "assignment_ids": self.assignment_ids,
            "skeleton_variants": [v.serialize() for v in self.skeleton_variants],
        }
