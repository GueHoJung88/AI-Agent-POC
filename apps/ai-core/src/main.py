# kpmg-ai-poc/apps/ai-core/src/main.py

import time
import uuid
import json

from fastapi import FastAPI
from db import get_conn
from settings import settings
from schemas import (
    ChatRequest, ChatResponse,
    ReportRequest, ReportResponse,
    FeedbackRequest, Citation
)
from agent import route_doc_group, copilot_answer, report_agent

app = FastAPI(title="KPMG AI PoC - AI Core", version="1.0")

def _score_stats(scores: list[float]):
    """avg/min/p95 계산(데이터 없으면 None)."""
    if not scores:
        return None, None, None
    s = sorted(scores)
    avg = sum(s) / len(s)
    mn = s[0]
    idx = int((0.95 * len(s)) - 1)
    idx = max(0, min(idx, len(s) - 1))
    p95 = s[idx]
    return avg, mn, p95

def log_query(
    *,
    trace_id: str,
    user_id: str,
    user_role: str | None,
    question: str,
    doc_group: str | None,
    top_k: int | None,
    prompt_version: str | None,
    answer: str | None,
    error: str | None,
    latency_ms: int | None,
    citations_payload: dict,
):
    """
    rag_query_log 실제 스키마(사용자 제공) 기준 INSERT.

    create table rag_query_log(
      id uuid pk,
      created_at timestamptz default now(),
      trace_id text,
      user_id text,
      user_role text,
      question text not null,
      doc_group text,
      top_k integer,
      embed_model_name text,
      llm_model text,
      prompt_version text,
      retrieval_count integer,
      retrieval_score_avg double precision,
      retrieval_score_min double precision,
      retrieval_score_p95 double precision,
      empty_retrieval boolean default false,
      answer text,
      evidences jsonb,
      latency_ms integer,
      citation_coverage double precision,
      context_overlap double precision,
      error text
    );
    """
    query_log_id = str(uuid.uuid4())

    scores = []
    for c in citations_payload.get("citations", []):
        try:
            scores.append(float(c.get("score", 0.0)))
        except Exception:
            pass

    retrieval_count = len(scores)
    avg, mn, p95 = _score_stats(scores)
    empty_retrieval = (retrieval_count == 0)

    # START: 실제 테이블 컬럼명(retrieval_count) 반영 + evidences(jsonb)
    sql = """
    INSERT INTO rag_query_log (
        id,
        trace_id,
        user_id,
        user_role,
        question,
        doc_group,
        top_k,
        embed_model_name,
        llm_model,
        prompt_version,
        retrieval_count,
        retrieval_score_avg,
        retrieval_score_min,
        retrieval_score_p95,
        empty_retrieval,
        answer,
        evidences,
        latency_ms,
        error
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s,
        %s,
        %s,
        %s::jsonb,
        %s,
        %s
    );
    """
    # END: 실제 테이블 컬럼 반영

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                query_log_id,
                trace_id,
                user_id,
                user_role,
                question,
                doc_group,
                top_k,
                getattr(settings, "embedding_model_name", None),
                # llm_model은 azure deployment 이름을 기록(현재 PoC 기준)
                getattr(settings, "azure_deployment", None),
                prompt_version,
                retrieval_count,
                avg,
                mn,
                p95,
                empty_retrieval,
                answer,
                json.dumps(citations_payload),
                latency_ms,
                error
            ))

    return query_log_id

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    trace_id = str(uuid.uuid4())
    t0 = time.time()

    doc_group = req.doc_group or route_doc_group(req.question, settings.default_doc_group)

    try:
        answer, chunks = copilot_answer(req.question, doc_group, req.top_k)
        t1 = time.time()

        citations = [
            Citation(
                doc_title=c["doc_title"],
                page=c.get("page"),
                file_path=c.get("file_path"),
                score=c["score"]
            )
            for c in chunks
        ]

        citations_payload = {"citations": [c.model_dump() for c in citations]}
        t_total_ms = int((t1 - t0) * 1000)

        # START: query_log_id 생성/반환 (정석: 응답에 포함)
        query_log_id = log_query(
            trace_id=trace_id,
            user_id=req.user_id,
            user_role=None,
            question=req.question,
            doc_group=doc_group,
            top_k=req.top_k,
            prompt_version="v1",
            answer=answer,
            error=None,
            latency_ms=t_total_ms,
            citations_payload=citations_payload,
        )
        # END: query_log_id 생성/반환

        return ChatResponse(
            trace_id=trace_id,
            doc_group=doc_group,
            answer=answer,
            citations=citations,
            timings={"total_ms": t_total_ms},
            # START: 응답에 query_log_id 포함
            query_log_id=query_log_id,
            # END: 응답에 query_log_id 포함
        )

    except Exception as e:
        t1 = time.time()
        t_total_ms = int((t1 - t0) * 1000)

        # START: 로깅 실패가 본 에러를 덮지 않도록 보호
        try:
            log_query(
                trace_id=trace_id,
                user_id=req.user_id,
                user_role=None,
                question=req.question,
                doc_group=doc_group,
                top_k=req.top_k,
                prompt_version="v1",
                answer=None,
                error=str(e),
                latency_ms=t_total_ms,
                citations_payload={"citations": []},
            )
        except Exception:
            pass
        # END: 로깅 보호
        raise

@app.post("/report", response_model=ReportResponse)
def report(req: ReportRequest):
    trace_id = str(uuid.uuid4())
    t0 = time.time()

    base_group = req.doc_group or settings.default_doc_group

    try:
        report_json, chunks, used_group = report_agent(req.scenario, base_group, req.top_k)
        t1 = time.time()

        citations = [
            Citation(
                doc_title=c["doc_title"],
                page=c.get("page"),
                file_path=c.get("file_path"),
                score=c["score"]
            )
            for c in chunks
        ]

        citations_payload = {
            "citations": [c.model_dump() for c in citations],
            "report_doc_group": used_group
        }

        t_total_ms = int((t1 - t0) * 1000)

        # START: report도 query_log_id 생성/반환
        query_log_id = log_query(
            trace_id=trace_id,
            user_id=req.user_id,
            user_role=None,
            question=req.scenario,   # question 컬럼에 scenario 저장 (PoC 방식 유지)
            doc_group=used_group,
            top_k=req.top_k,
            prompt_version="report_v1",
            answer=json.dumps(report_json) if not isinstance(report_json, str) else report_json,
            error=None,
            latency_ms=t_total_ms,
            citations_payload=citations_payload,
        )
        # END: report도 query_log_id 생성/반환

        return ReportResponse(
            trace_id=trace_id,
            doc_group=used_group,
            report_json=report_json,
            citations=citations,
            timings={"total_ms": t_total_ms},
            # START: 응답에 query_log_id 포함
            query_log_id=query_log_id,
            # END: 응답에 query_log_id 포함
        )

    except Exception as e:
        t1 = time.time()
        t_total_ms = int((t1 - t0) * 1000)

        # START: 로깅 보호
        try:
            log_query(
                trace_id=trace_id,
                user_id=req.user_id,
                user_role=None,
                question=req.scenario,
                doc_group=base_group,
                top_k=req.top_k,
                prompt_version="report_v1",
                answer=None,
                error=str(e),
                latency_ms=t_total_ms,
                citations_payload={"citations": []},
            )
        except Exception:
            pass
        # END: 로깅 보호
        raise

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    """
    rag_feedback 실제 스키마(사용자 제공) 기준 INSERT:

    create table rag_feedback(
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
    );
    """

    # START: DB 스키마 반영 - 컬럼명/타입 일치
    sql = """
    INSERT INTO rag_feedback (
        id,
        query_log_id,
        user_id,
        rating,
        is_helpful,
        feedback_text,
        tags,
        expected_answer,
        chosen_evidence_ids
    )
    VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
    """
    # END: DB 스키마 반영

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                str(uuid.uuid4()),
                str(req.query_log_id),
                req.user_id,
                req.rating,
                req.is_helpful,
                req.feedback_text,
                req.tags,  # psycopg가 text[]로 변환 처리
                req.expected_answer,
                [str(x) for x in req.chosen_evidence_ids] if req.chosen_evidence_ids else None
            ))

    return {"ok": True}
