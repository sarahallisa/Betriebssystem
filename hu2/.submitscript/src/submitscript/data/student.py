from typing import Optional, Union, Dict, List

from submitscript.util.serialize import SerializableData


class Student(SerializableData):
    """
    Represents a student with their name and matriculation number
    """

    def __init__(self, last_name: str, first_name: str, matriculation_number: str):
        self.first_name = first_name
        self.last_name = last_name
        self.matriculation_number = matriculation_number

    def __str__(self):
        return str((self.last_name, self.first_name, self.matriculation_number))

    def __eq__(self, other: 'Student'):
        return other is Student and self.matriculation_number == other.matriculation_number

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> Optional['Student']:
        """
        Deserializes a student from a Dict
        :param obj: A Dict representing a Student
        :return: The deserialized Student
        """
        cls.require_type(obj, dict)

        return Student(
            obj["last_name"],
            obj["first_name"],
            obj["matriculation_number"])

    def serialize(self) -> Union[Dict, List]:
        """
        Converts this Student to a serialized Dict
        :return: The serialized Dict
        """
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "matriculation_number": self.matriculation_number
        }
