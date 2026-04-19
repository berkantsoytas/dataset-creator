from dataclasses import dataclass
from typing import Optional


@dataclass
class CodeChunk:
    id: str
    path: str
    language: str
    chunk_type: str
    name: str
    code: str
    start_line: int
    end_line: int
    explanation: str
    time_complexity: Optional[str]
    quality_score: Optional[float] = None
