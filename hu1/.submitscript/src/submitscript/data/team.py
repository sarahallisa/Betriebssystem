from typing import List, Union, Dict

from submitscript.data.student import Student
from submitscript.util.serialize import SerializableData


class Team(SerializableData):
    def __init__(self, members: List[Student]):
        self.members = members

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'Team':
        cls.require_type(obj, list)

        return Team([Student.deserialize(s) for s in obj])

    def serialize(self) -> Union[Dict, List]:
        return [m.serialize() for m in self.members]

    def size(self):
        return len(self.members)

    def __contains__(self, item: Student):
        return item in self.members

    def intersect(self, other: 'Team') -> List[Student]:
        return [s for s in self.members if s in other]
