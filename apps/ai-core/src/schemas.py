from pydantic import BaseModel
from typing import Any, Optional

class ChatRequest(BaseModel):
    user_id: str = "demo"
    question: str
    doc_group: Optional[str] = None
    top_k: int = 8

class Citation(BaseModel):
    doc_title: str
    page: int | None = None
    file_path: str | None = None
    score: float

class ChatResponse(BaseModel):
    trace_id: str
    doc_group: str
    answer: str
    citations: list[Citation]
    timings: dict[str, Any]

class ReportRequest(BaseModel):
    user_id: str = "demo"
    scenario: str
    doc_group: Optional[str] = None
    top_k: int = 10

class ReportResponse(BaseModel):
    trace_id: str
    doc_group: str
    report_json: str
    citations: list[Citation]
    timings: dict[str, Any]

class FeedbackRequest(BaseModel):
    query_log_id: str
    rating: int | None = None
    is_helpful: bool | None = None
    is_grounded: bool | None = None
    comment: str | None = None

