import datetime
from pathlib import Path
from typing import List, Optional, TextIO

from submitscript.api.api import Backend, CourseRoutes
from submitscript.data.assignment import Assignment
from submitscript.data.config import Config
from submitscript.data.team import Team
from submitscript.util.properties import TextFileProperty


class DataDirectory:
    def __init__(self, path: Path):
        self.path = path
        self.team = TextFileProperty(path / "team.json").json_serialized(Team)
        self.config = TextFileProperty(path / "config.json").json_serialized(Config)
        self.assignments_path = path / "assignments"

        self.logs_path = path / "logs"

    def create_logfile(self) -> TextIO:
        self.logs_path.mkdir(parents=True, exist_ok=True)

        return (self.logs_path / datetime.datetime.now().strftime('log%y-%m-%dT%H_%M_%S.log')).open("w")

    def get_assignment(self, assignment_id: str) -> Optional['Assignment']:
        if assignment_id not in self.config.get().assignment_ids:
            return None

        assignment = Assignment(self, assignment_id, self.assignments_path / assignment_id)

        if not assignment.path.is_dir():
            assignment.path.mkdir(parents=True, exist_ok=True)

        return assignment

    def get_assignments(self) -> List[Assignment]:
        return [self.get_assignment(i) for i in self.config.get().assignment_ids]

    def get_backend(self) -> Backend:
        return Backend(self.config.get().server)

    def get_course_backend(self) -> CourseRoutes:
        return self.get_backend().courses[self.config.get().course_name]
