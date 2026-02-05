import time, uuid, json
from fastapi import FastAPI
from db import get_conn
from settings import settings
from schemas import ChatRequest, ChatResponse, ReportRequest, ReportResponse, FeedbackRequest, Citation
from agent import route_doc_group, copilot_answer, report_agent

app = FastAPI(title="KPMG AI PoC - AI Core", version="1.0")

def log_query(trace_id: str, user_id: str, question: str, doc_group: str, top_k: int,
              retrieved_meta: dict, model_name: str, prompt_version: str,
              answer: str | None, error: str | None,
              t_retrieval_ms: int, t_generate_ms: int, t_total_ms: int):
    sql = """
    INSERT INTO rag_query_log (
        id, trace_id, user_id, question, doc_group, top_k, retrieved_count, retrieved_meta,
        model_name, prompt_version, answer, error, t_retrieval_ms, t_generate_ms, t_total_ms
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                str(uuid.uuid4()), trace_id, user_id, question, doc_group, top_k,
                len(retrieved_meta.get("citations", [])),
                json.dumps(retrieved_meta),
                model_name, prompt_version,
                answer, error,
                t_retrieval_ms, t_generate_ms, t_total_ms
            ))

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    trace_id = str(uuid.uuid4())
    t0 = time.time()

    doc_group = req.doc_group or route_doc_group(req.question, settings.default_doc_group)

    try:
        t_retr_start = time.time()
        answer, chunks = copilot_answer(req.question, doc_group, req.top_k)
        t1 = time.time()

        citations = [
            Citation(doc_title=c["doc_title"], page=c.get("page"), file_path=c.get("file_path"), score=c["score"])
            for c in chunks
        ]
        retrieved_meta = {"citations": [c.model_dump() for c in citations]}

        # 대략 generate 시간(여기선 retrieval+generate가 섞여 있지만 PoC니까 분리값만 제공)
        t_total_ms = int((t1 - t0) * 1000)
        t_retrieval_ms = int((t1 - t_retr_start) * 1000)
        t_generate_ms = max(0, t_total_ms - t_retrieval_ms)

        log_query(
            trace_id=trace_id,
            user_id=req.user_id,
            question=req.question,
            doc_group=doc_group,
            top_k=req.top_k,
            retrieved_meta=retrieved_meta,
            model_name=settings.azure_deployment,
            prompt_version="v1",
            answer=answer,
            error=None,
            t_retrieval_ms=t_retrieval_ms,
            t_generate_ms=t_generate_ms,
            t_total_ms=t_total_ms
        )

        return ChatResponse(
            trace_id=trace_id,
            doc_group=doc_group,
            answer=answer,
            citations=citations,
            timings={"total_ms": t_total_ms, "retrieval_ms": t_retrieval_ms, "generate_ms": t_generate_ms},
        )
    except Exception as e:
        t1 = time.time()
        t_total_ms = int((t1 - t0) * 1000)
        log_query(
            trace_id=trace_id,
            user_id=req.user_id,
            question=req.question,
            doc_group=doc_group,
            top_k=req.top_k,
            retrieved_meta={},
            model_name=settings.azure_deployment,
            prompt_version="v1",
            answer=None,
            error=str(e),
            t_retrieval_ms=0,
            t_generate_ms=0,
            t_total_ms=t_total_ms
        )
        raise

@app.post("/report", response_model=ReportResponse)
def report(req: ReportRequest):
    trace_id = str(uuid.uuid4())
    t0 = time.time()

    base_group = req.doc_group or settings.default_doc_group

    t_retr_start = time.time()
    report_json, chunks, used_group = report_agent(req.scenario, base_group, req.top_k)
    t1 = time.time()

    citations = [
        Citation(doc_title=c["doc_title"], page=c.get("page"), file_path=c.get("file_path"), score=c["score"])
        for c in chunks
    ]
    retrieved_meta = {"citations": [c.model_dump() for c in citations], "report_doc_group": used_group}

    t_total_ms = int((t1 - t0) * 1000)
    t_retrieval_ms = int((t1 - t_retr_start) * 1000)
    t_generate_ms = max(0, t_total_ms - t_retrieval_ms)

    # 보고서도 query_log에 남김(질문=시나리오)
    log_query(
        trace_id=trace_id,
        user_id=req.user_id,
        question=req.scenario,
        doc_group=used_group,
        top_k=req.top_k,
        retrieved_meta=retrieved_meta,
        model_name=settings.azure_deployment,
        prompt_version="report_v1",
        answer=report_json,
        error=None,
        t_retrieval_ms=t_retrieval_ms,
        t_generate_ms=t_generate_ms,
        t_total_ms=t_total_ms
    )

    return ReportResponse(
        trace_id=trace_id,
        doc_group=used_group,
        report_json=report_json,
        citations=citations,
        timings={"total_ms": t_total_ms, "retrieval_ms": t_retrieval_ms, "generate_ms": t_generate_ms},
    )

@app.post("/feedback")
def feedback(req: FeedbackRequest):
    sql = """
    INSERT INTO rag_feedback (id, query_log_id, rating, is_helpful, is_grounded, comment)
    VALUES (%s, %s, %s, %s, %s, %s);
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (
                str(uuid.uuid4()),
                req.query_log_id,
                req.rating,
                req.is_helpful,
                req.is_grounded,
                req.comment
            ))
    return {"ok": True}

