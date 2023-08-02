from typing import Optional, Union, Dict, List

from submitscript.util.serialize import SerializableData


class EvaluationResult(SerializableData):
    """
    Represents the result of the evaluation of a submission
    """

    def __init__(self, score: int, max_score: int, passed: bool, fixed: bool = False, log: Optional[str] = None, comment: Optional[str] = None):
        self.score = score
        self.max_score = max_score
        self.passed = passed
        self.fixed = fixed
        self.comment = comment
        self.log = log

    @classmethod
    def deserialize_impl(cls, obj: Union[Dict, List]) -> 'EvaluationResult':
        """
        Deserializes an EvaluationResult from a Dict
        :param obj: A Dict representing an EvaluationResult
        :return: The deserialized EvaluationResult
        """
        cls.require_type(obj, dict)

        return EvaluationResult(
            obj["score"],
            obj["max_score"],
            obj["passed"],
            obj.get("fixed", False),  # Optional to ensure backwards compatibility
            obj.get("log"),
            obj.get("comment"))

    def serialize(self) -> Union[Dict, List]:
        """
        Converts this EvaluationResult to a serialized Dict
        :return: The serialized Dict
        """
        return {
            "score": self.score,
            "max_score": self.max_score,
            "passed": self.passed,
            "fixed": self.fixed,
            "log": self.log,
            "comment": self.comment
        }

    def valid(self) -> bool:
        """
        An evaluation result is considered consistent when the max_score is more than zero and the actual score is inside [0, max_score]

        :return: Whether this evaluation result is consistent.
        """
        return 0 < self.max_score \
               and 0 <= self.score <= self.max_score

    def score_fraction(self):
        """
        :return: The fraction of passed test cases in the range [0, 1]
        """
        if self.max_score == 0:
            return 0

        return self.score / self.max_score
