import re
from settings import settings
from embeddings import embed_query
from rag import retrieve_pgvector, build_context
from llm_azure import chat_completion

def route_doc_group(question: str, default_group: str) -> str:
    q = question.lower()

    if any(k in q for k in ["llm", "ai", "생성형", "모델", "학습", "프롬프트", "agent", "copilot"]):
        return "ai_guideline"
    if any(k in q for k in ["동의", "제3자", "위탁", "파기", "보유", "처리", "제공", "법", "조항"]):
        return "law"
    if any(k in q for k in ["사례", "해석", "판단", "질의응답", "q&a", "FAQ".lower()]):
        return "commentary"
    return default_group

def copilot_answer(question: str, doc_group: str, top_k: int):
    qvec = embed_query(question)
    chunks = retrieve_pgvector(qvec, doc_group=doc_group, top_k=top_k)
    context = build_context(chunks)

    system = (
        "너는 개인정보보호 컴플라이언스 어시스턴트다.\n"
        "반드시 제공된 근거(context) 범위 안에서만 답해라.\n"
        "근거가 부족하면 '근거 부족'이라고 말하고 추가 질문을 제안해라.\n"
        "답변 마지막에 '근거' 섹션을 만들어 문서명/페이지를 bullet로 제시해라."
    )
    user = f"질문:\n{question}\n\n근거(context):\n{context}"
    answer = chat_completion(system, user)
    return answer, chunks

def report_agent(scenario: str, base_group: str, top_k: int):
    # 조사(Research): 질문 확장 + 근거 수집
    q = f"{scenario}\n(개인정보보호 관점에서 쟁점/요건/위험을 중심으로)"
    doc_group = route_doc_group(q, base_group)

    qvec = embed_query(q)
    chunks = retrieve_pgvector(qvec, doc_group=doc_group, top_k=top_k)
    context = build_context(chunks, max_chars=8000)

    # 작성(Writer): JSON 보고서
    system = (
        "너는 컨설팅 보고서 작성 AI다.\n"
        "출력은 반드시 JSON 하나만 반환한다.\n"
        "스키마:\n"
        "{"
        "\"summary\": string,"
        "\"risks\": [{\"title\": string, \"detail\": string, \"severity\": \"low|medium|high\"}],"
        "\"requirements\": [string],"
        "\"recommended_actions\": [string],"
        "\"checklist\": [string]"
        "}\n"
        "근거(context)에 없는 내용은 단정하지 말고 '추정' 표시를 하거나 제외해라."
    )
    user = f"시나리오:\n{scenario}\n\n근거(context):\n{context}"
    report_json = chat_completion(system, user, max_tokens=1100, temperature=0.1)

    # 검증(Verifier): 근거 포함률/금칙어 간단 체크(여기선 PoC용 최소)
    # 실제는 PII/정책 위반 룰셋을 강화.
    return report_json, chunks, doc_group
