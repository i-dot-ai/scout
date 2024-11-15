from typing import List

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_anonymizer import AnonymizerEngine, EngineResult
from presidio_anonymizer.entities import OperatorConfig


class ConsistentPersonOperator:
    """Means that if a name comes up multiple times they are name consistently
    Expansion idea: use LLM to infer names of people (e.g SRO)
    """

    def __init__(self):
        self.person_map = {}
        self.counter = 1

    def __call__(self, text, **kwargs):
        if text not in self.person_map:
            self.person_map[text] = f"<Person {self.counter}>"
            self.counter += 1
        return self.person_map[text]


class Anonymizer:
    """Anonmyizes chunks using presidio"""

    def __init__(self) -> None:
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        consistent_person_operator = ConsistentPersonOperator()
        self.operators = {
            "PERSON": OperatorConfig("custom", {"lambda": consistent_person_operator}),
            "PHONE_NUMBER": OperatorConfig("mask", {"chars_to_mask": 6, "masking_char": "*", "from_end": True}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL>"}),
        }

    def analyze(self, text: str) -> List[RecognizerResult]:
        return self.analyzer.analyze(
            text=text,
            language="en",
            entities=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"],
            score_threshold=0.8,
        )

    def anonymize(self, text: str) -> EngineResult:
        analyzer_results = self.analyze(text)
        return self.anonymizer.anonymize(text, analyzer_results, operators=self.operators)
