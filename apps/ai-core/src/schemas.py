from pydantic import BaseModel, Field
from typing import Any, Optional, List
from uuid import UUID

class ChatRequest(BaseModel):
    user_id: str = "demo"
    question: str
    doc_group: Optional[str] = None
    top_k: int = 8

class Citation(BaseModel):
    doc_title: str
    page: int | None = None
    # START: API 호환 유지 - 내부는 doc_path지만 응답은 file_path로 내려감
    file_path: Optional[str] = None
    # END: API 호환 유지
    score: float

class ChatResponse(BaseModel):
    trace_id: str
    doc_group: str
    answer: str
    citations: list[Citation]
    timings: dict[str, Any]
    # START: feedback 정석 지원 - query_log_id 포함
    query_log_id: str
    # END: feedback 정석 지원

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
    # START: feedback 정석 지원 - query_log_id 포함
    query_log_id: str
    # END: feedback 정석 지원

class FeedbackRequest(BaseModel):
    """
    rag_feedback 테이블 스키마(사용자 제공) 반영:
      rag_feedback(
        id uuid pk,
        created_at timestamptz default now(),
        query_log_id uuid not null references rag_query_log on delete cascade,
        user_id text,
        rating integer,
        is_helpful boolean,
        feedback_text text,
        tags text[],
        expected_answer text,
        chosen_evidence_ids uuid[]
      )
    """
    query_log_id: UUID
    user_id: Optional[str] = None
    rating: Optional[int] = None
    is_helpful: Optional[bool] = None

    # START: DB 스키마 반영 필드
    feedback_text: Optional[str] = None
    tags: Optional[List[str]] = None
    expected_answer: Optional[str] = None
    chosen_evidence_ids: Optional[List[UUID]] = None
    # END: DB 스키마 반영 필드

