import datetime
from typing import TextIO, Optional


class LogFile:
    def __init__(self, file: TextIO, also_log_to: Optional['LogFile'] = None, flush_after_log: bool = False):
        self.file = file
        self.flush_after_log = flush_after_log
        self.also_log_to = also_log_to

    def write(self, text: str):
        if self.also_log_to is not None:
            self.also_log_to.write(text)

        self.file.write(text)

        if self.flush_after_log:
            self.file.flush()

    def log_with_time(self, message: str, time: datetime.datetime):
        self.write("[%s] %s\n" % (time, message))

    def log(self, message: str):
        self.log_with_time(message, datetime.datetime.now())

    def error(self, message: str):
        self.log("Error: %s" % message)

    def skip_line(self):
        self.write("\n")

    @staticmethod
    def stderr():
        import sys
        return LogFile(sys.stderr, flush_after_log=True)

    @staticmethod
    def stdout():
        import sys
        return LogFile(sys.stdout, flush_after_log=True)

    @staticmethod
    def devnull():
        import os
        return LogFile(open(os.devnull, "w"))
