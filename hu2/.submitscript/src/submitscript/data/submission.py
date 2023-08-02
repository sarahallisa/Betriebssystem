from enum import Enum
from pathlib import Path
from typing import Union, Dict, List, Optional

from typing.io import IO

from submitscript import data
from submitscript.api.api import SubmissionRoutes
from submitscript.api.types import ApiSerializableSubmissionResponse, ApiSerializableSubmission
from submitscript.data.team import Team
from submitscript.output import interface_print
from submitscript.util.prompt import prompt, YesNoParser
from submitscript.util.properties import TextFileProperty, JsonProperty, Property
from submitscript.util.serialize import SerializableData, deserialize_enum, serialize_enum


class SubmissionStatus(Enum):
    in_construction = "in_construction"
    rejected = "rejected"
    accepted = "accepted"
    removed = "removed"
    evaluated = "evaluated"

    @staticmethod
    def deserialize(obj: str) -> 'SubmissionStatus':
        return deserialize_enum(SubmissionStatus, obj)

    def serialize(self) -> str:
        return serialize_enum(self)


class SubmissionBookkeeping(SerializableData):
    def __init__(self, status: SubmissionStatus):
        self.status = status

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'SubmissionBookkeeping':
        SubmissionBookkeeping.require_type(obj, dict)

        return SubmissionBookkeeping(
            SubmissionStatus.deserialize(obj["status"])
        )

    def serialize(self) -> Union[Dict, List]:
        return {
            "status": self.status.serialize()
        }


class Submission:
    def __init__(self, parent: 'data.Assignment', path: Path):
        self.parent = parent
        self.path = path

        # Paths for files used when uploading the submission
        self.team: JsonProperty[Team] = TextFileProperty(self.path / "team.json").json_serialized(Team)
        self.variant = TextFileProperty(path / "variant.json").json_serialized()
        self.upload_tgz_path = path / "upload.tgz"

        # Paths for files that relate to the submission response or evaluation result
        self.bookkeeping_data: Property[SubmissionBookkeeping] = TextFileProperty(path / "bookkeeping.json").json_serialized(SubmissionBookkeeping).cached()
        self.submission_data: Property[ApiSerializableSubmission] = TextFileProperty(path / "submission.json").json_serialized(ApiSerializableSubmission).cached()
        self.submission_response = TextFileProperty(path / "submission_response.json").json_serialized(ApiSerializableSubmissionResponse).cached()
        self.evaluation_log = TextFileProperty(path / "evaluation.log")
        self.submission_log = TextFileProperty(path / "submit.log")

    def delete(self):
        import shutil
        shutil.rmtree(self.path)

    def set_upload_file(self, file: IO[bytes]) -> None:
        file.seek(0)

        import shutil
        shutil.copyfileobj(file, self.upload_tgz_path.open("wb"))

    def rename(self, name: str):
        # This workaround is needed because Path.rename does not return the new path in python version before 3.8
        new_path = self.path.with_name(name)
        self.path.rename(new_path)

        # Recall __init__ to update all property paths
        self.__init__(self.parent, new_path)

    def update_name(self, new_id: Optional[str] = None):
        import re
        matched = re.search("(\[(.*)])?\s*(.+)", self.path.name)
        tag = matched.group(2)
        old_id = matched.group(3)

        self.rename("[%s] %s" % (self.bookkeeping_data.get().status.value, new_id or old_id))

    def set_status(self, status: SubmissionStatus, new_id: Optional[str] = None):
        bookkeeping = self.bookkeeping_data.get()
        if bookkeeping is None:
            bookkeeping = SubmissionBookkeeping(status)
        else:
            bookkeeping.status = status

        self.bookkeeping_data.set(bookkeeping)
        self.update_name(new_id)

    def submit(self) -> bool:
        interface_print("=== Starting Upload ===")
        self.submission_response.set(self.parent.get_backend().submissions.post(self.upload_tgz_path, self.variant.base_property.get(), self.team.base_property.get()))
        self.submission_data.set(self.submission_response.get().submission)
        self.submission_log.set(self.submission_response.get().log)

        interface_print("=== Upload finished ===")
        interface_print("=== BEGIN Upload Log")
        interface_print(self.submission_response.get().log)
        interface_print("=== END Upload Log")

        if not self.submission_response.get().accepted:
            interface_print("Submitting your solution failed. Please see the upload log above for more details.")
            self.set_status(SubmissionStatus.rejected)
            return False
        else:
            interface_print("Successfully submitted your solution. Please see the upload log above for more details.")
            self.set_status(SubmissionStatus.accepted, self.submission_response.get().submission.submission_id)

            if self.submission_response.get().immediate_evaluation:
                self.wait_for_evaluation_results()

            return True

    def prompt_evaluation_wait(self):
        if not self.submission_response.has_value() or not self.submission_response.get().immediate_evaluation:
            return

        if prompt("This submission will be evaluated immediately. Do you want to wait for results now?", YesNoParser(True)):
            self.wait_for_evaluation_results()

    def check_for_evaluation_results(self) -> Optional[bool]:
        if not self.bookkeeping_data.has_value():
            interface_print("Error: There appears to be a data corruption. Bookkeeping data for a submission are missing.")
            return None

        if self.bookkeeping_data.get().status != SubmissionStatus.accepted:
            interface_print("Error: Can only check for results of accepted submissions. Please report this as a bug in the script.")
            return None

        evaluated = self.get_backend().is_evaluated()

        if evaluated is None:
            interface_print("- Submission '%s' can no longer be found on the server and will be marked as [removed]." % self.submission_data.get().submission_id)
            self.set_status(SubmissionStatus.removed)
            return None
        elif evaluated:
            self.submission_data.set(self.get_backend().get(True))
            self.evaluation_log.set(self.submission_data.get().evaluation_result.log)

            self.set_status(SubmissionStatus.evaluated)

            interface_print("\n=== Evaluation results for submission '%s' retrieved. ===" % self.submission_data.get().submission_id)

            return True

        return False

    def print_evaluation_results(self) -> None:
        score_percentage = \
            100 * self.submission_data.get().evaluation_result.score / self.submission_data.get().evaluation_result.max_score \
                if self.submission_data.get().evaluation_result.max_score != 0 \
                else 0

        interface_print("You achieved the score %d/%d (%d%%)." % (self.submission_data.get().evaluation_result.score,
                                                        self.submission_data.get().evaluation_result.max_score,
                                                        score_percentage))

        if self.submission_data.get().evaluation_result.comment is not None:
            interface_print("The following comment was left by your teacher:")
            interface_print(self.submission_data.get().evaluation_result.comment)

        if self.submission_data.get().evaluation_result.passed:
            interface_print("You have PASSED this assignment.")
        else:
            interface_print("You have NOT PASSED this assignment.")

        if self.submission_data.get().evaluation_result.log is not None:
            if prompt("Do you want to view the evaluation log now?", YesNoParser(True)):
                interface_print("=== BEGIN Evaluation Log")
                interface_print(self.submission_data.get().evaluation_result.log)
                interface_print("=== END Evaluation Log")

        interface_print("NOTE: This evaluation log is also available at '%s'" % self.evaluation_log.path.absolute())

    def wait_for_evaluation_results(self) -> bool:
        interface_print("Polling for results (Press CTRL + C to abort).", end="")

        try:
            import time

            while True:
                results_found = self.check_for_evaluation_results()

                if results_found:
                    self.print_evaluation_results()
                    break
                if results_found is None:
                    break

                interface_print(".", end="", flush=True)
                time.sleep(1)

        except KeyboardInterrupt:
            interface_print("\nResult polling aborted.")

        return True

    def get_backend(self) -> SubmissionRoutes:
        return self.parent.get_backend().submissions[self.submission_data.get().submission_id]
