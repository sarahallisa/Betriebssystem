from pathlib import Path
from typing import Dict, Optional

import requests
import semver

from submitscript.api.types import ApiSerializableSubmissionResponse, ApiSerializableSubmission
from submitscript.data.config import Server


class SubmissionRoutes:
    def __init__(self, parent: 'SubmissionsRoutes', submission_id: str):
        self.parent = parent
        self.base_url = parent.base_url + ("/%s" % submission_id)

    def is_evaluated(self) -> Optional[bool]:
        result = requests.get(self.base_url + "/m/is_evaluated")

        if result.status_code == 404:
            return None

        return result.json()

    def get(self, include_eval_log: bool) -> ApiSerializableSubmission:
        return ApiSerializableSubmission.deserialize(requests.get(self.base_url, params={"include_eval_log": include_eval_log}).json())


class SubmissionsRoutes:
    def __init__(self, parent: 'AssignmentRoutes'):
        self.parent = parent
        self.base_url = parent.base_url + "/submissions"

    def __getitem__(self, submission_id: str) -> SubmissionRoutes:
        return SubmissionRoutes(self, submission_id)

    def post(self, archive_path: Path, variant_json_text: str, team_json_text: str) -> ApiSerializableSubmissionResponse:
        with archive_path.open("rb") as archive_stream:
            response = requests.post(self.base_url,
                                     files={
                                         "archive": ("upload.tgz", archive_stream)
                                     },
                                     data={
                                         "variant": variant_json_text,
                                         "team": team_json_text
                                     })

            return ApiSerializableSubmissionResponse.deserialize(response.json())


class AssignmentRoutes:
    def __init__(self, parent: 'AssignmentsRoutes', assignment_id: str):
        self.parent = parent
        self.base_url = parent.base_url + ("/%s" % assignment_id)

        self.submissions = SubmissionsRoutes(self)


class AssignmentsRoutes:
    def __init__(self, parent: 'CourseRoutes'):
        self.parent = parent
        self.base_url = parent.base_url + "/assignments"

    def __getitem__(self, assignment_id: str) -> AssignmentRoutes:
        return AssignmentRoutes(self, assignment_id)


class CourseRoutes:
    def __init__(self, parent: 'CoursesRoutes', course_id: str):
        self.parent = parent
        self.base_url = parent.base_url + ("/%s" % course_id)

        self.assignments = AssignmentsRoutes(self)


class CoursesRoutes:
    def __init__(self, parent: 'Backend'):
        self.parent = parent

        self.base_url = parent.base_url + "/courses"

    def __getitem__(self, course_id: str) -> CourseRoutes:
        return CourseRoutes(self, course_id)


class ClientRoutes:
    def __init__(self, parent: 'Backend'):
        self.parent = parent

        self.base_url = parent.base_url + "/client"

    def get(self):
        return requests.get(self.base_url).content

    def get_current_version(self):
        return semver.parse(requests.get(self.base_url + "/current_version").text)

    def get_changelogs(self) -> Dict:
        res = {}
        for k, v in requests.get(self.base_url + "/changelogs").json().items():
            res[semver.VersionInfo.parse(k)] = v
        return res


class Backend:
    def __init__(self, server: Server):
        self.server = server
        self.base_url = "%s/api" % server.to_url()

        self.courses = CoursesRoutes(self)
        self.client = ClientRoutes(self)
