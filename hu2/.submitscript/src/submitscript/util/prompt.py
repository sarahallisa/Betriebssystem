from abc import ABC, abstractmethod
from typing import Optional, Any, Tuple, List

from submitscript.output import interface_print


class InputParser(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_format_description(self):
        return ""

    @abstractmethod
    def parse(self, inp: str):
        pass


class YesNoParser(InputParser):
    def __init__(self, default: bool = True):
        super().__init__()
        self.default = default

    def parse(self, inp: str) -> Optional[bool]:
        if len(inp) == 0:
            return self.default
        if inp in ["Y", "y"]:
            return True
        if inp in ["N", "n"]:
            return False
        return None

    def get_format_description(self):
        if self.default:
            return "[Y/n]"
        else:
            return "[y/N]"


class NameParser(InputParser):

    def get_format_description(self):
        return ""

    def parse(self, inp: str):
        # No actual validation takes place
        return inp


class MatriculationNumberParser(InputParser):

    def get_format_description(self):
        return ""

    def parse(self, inp: str):
        if not inp.isnumeric():
            return None
        return inp


class SelectionParser(InputParser):

    def __init__(self, options: List[Tuple[str, Any]], default: Optional[int]):
        super().__init__()
        self.options = options
        self.default = default

    def get_format_description(self):
        desc = "\n"

        i = 1
        for option_str, option in self.options:
            desc += " %d - %s\n" % (i, option_str)
            i += 1

        desc += "Please enter the id of your selection"

        if self.default is not None:
            desc += " (Default: %d)" % self.default

        desc += ":"

        return desc

    def parse(self, inp: str):
        if inp.isnumeric():
            index = int(inp) - 1
            return self.options[index][1] if 0 <= index < len(self.options) else None

        return None


def prompt(description: str, input_parser: InputParser):
    while True:
        result = input_parser.parse(input("%s %s " % (description, input_parser.get_format_description())))

        if result is None:
            interface_print("Sorry, again.")
            continue

        return result
