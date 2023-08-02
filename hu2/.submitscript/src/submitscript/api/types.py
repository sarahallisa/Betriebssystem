from typing import Optional, Union, Dict, List

from submitscript.data.evaluation_result import EvaluationResult
from submitscript.data.team import Team
from submitscript.util.map_optional import map_optional
from submitscript.util.serialize import SerializableData


class ApiSerializableSubmission(SerializableData):
    def __init__(self, submission_id: str, team: Team, timestamp: int, upload_log: str, evaluation_result: Optional[EvaluationResult]):
        self.submission_id = submission_id
        self.team = team
        self.timestamp = timestamp
        self.upload_log = upload_log
        self.evaluation_result = evaluation_result

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'ApiSerializableSubmission':
        cls.require_type(obj, dict)

        return ApiSerializableSubmission(
            submission_id=obj["id"],
            team=Team.deserialize(obj["authors"]),
            timestamp=obj["timestamp_ns"],
            upload_log=obj["upload_log"],
            evaluation_result=map_optional(obj.get("evaluation_result"), EvaluationResult.deserialize)
        )

    def serialize(self) -> Union[Dict, List]:
        return {
            "id": self.submission_id,
            "authors": self.team.serialize(),
            "timestamp_ns": self.timestamp,
            "upload_log": self.upload_log,
            "evaluation_result": map_optional(self.evaluation_result, lambda e: e.serialize())
        }


class ApiSerializableSubmissionResponse(SerializableData):
    def __init__(self, accepted: bool, log: str, submission: Optional[ApiSerializableSubmission], immediate_evaluation: Optional[bool]):
        self.accepted = accepted
        self.log = log
        self.submission = submission
        self.immediate_evaluation = immediate_evaluation

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'ApiSerializableSubmissionResponse':
        cls.require_type(obj, dict)

        return ApiSerializableSubmissionResponse(
            obj["accepted"],
            obj["log"],
            map_optional(obj.get("submission"), ApiSerializableSubmission.deserialize_impl),
            obj.get("immediate_evaluation", None)
        )

    def serialize(self) -> Union[Dict, List]:
        return {
            "accepted": self.accepted,
            "log": self.log,
            "submission": map_optional(self.submission, lambda s: s.serialize()),
            "immediate_evaluation": self.immediate_evaluation
        }
