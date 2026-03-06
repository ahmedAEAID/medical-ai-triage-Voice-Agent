import logging
from dataclasses import dataclass

logger = logging.getLogger("medical-triage.models")

@dataclass
class IdentityDetails:
    name: str
    age: int

@dataclass
class SymptomDetails:
    primary_complaint: str
    duration_days: int
    severity_level: int