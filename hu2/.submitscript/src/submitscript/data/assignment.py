from pathlib import Path
from typing import List

from submitscript import data
from submitscript.api.api import AssignmentRoutes
from submitscript.data.submission import Submission, SubmissionStatus, SubmissionBookkeeping


class Assignment:
    def __init__(self, parent: 'data.DataDirectory', assignment_id: str, path: Path):
        self.parent = parent
        self.assignment_id = assignment_id
        self.path = path

        self.submissions_path = path / "submissions"

    def get_submissions(self) -> List[Submission]:
        if not self.submissions_path.exists():
            return []

        submissions = [Submission(self, path) for path in self.submissions_path.iterdir() if path.is_dir()]

        # Add bookkeeping data for legacy submissions that did not have one.
        for submission in submissions:
            if submission.bookkeeping_data.has_value():
                continue

            if submission.path.name.startswith("temp_submission"):
                submission.bookkeeping_data.set(SubmissionBookkeeping(SubmissionStatus.in_construction))
            elif submission.path.name.startswith("REJECTED"):
                submission.bookkeeping_data.set(SubmissionBookkeeping(SubmissionStatus.rejected))
            elif submission.submission_data.get().evaluation_result is not None:
                submission.bookkeeping_data.set(SubmissionBookkeeping(SubmissionStatus.evaluated))
            else:
                submission.bookkeeping_data.set(SubmissionBookkeeping(SubmissionStatus.accepted))

        return submissions

    def create_submission(self) -> Submission:
        import uuid

        path = self.submissions_path / ("%s" % uuid.uuid4())
        path.mkdir(parents=True, exist_ok=True)

        submission = Submission(self, path)
        submission.set_status(SubmissionStatus.in_construction)

        return submission

    def get_backend(self) -> AssignmentRoutes:
        return self.parent.get_course_backend().assignments[self.assignment_id]
