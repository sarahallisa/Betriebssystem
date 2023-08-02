import os
from typing.io import TextIO

from submitscript.util.logfile import LogFile

global_log_file = LogFile(open(os.devnull, "w"), flush_after_log=True)


def set_global_log_file(file: TextIO):
    global_log_file.file = file


def interface_print(s: str = "", flush: bool = False, end: str = "\n"):
    print(s, flush=flush, end=end)
    global_log_file.log(s)
