import time
from typing import Any
from db import get_conn

def retrieve_pgvector(query_vec: list[float], doc_group: str, top_k: int) -> list[dict[str, Any]]:
    """
    cosine distance: embedding <=> query_vec
    score = 1 - distance

    PostgreSQL + pgvector 기반 검색.

    DB 스키마(사용자 제공):
      rag_chunks(id, doc_title, doc_group, section, page, content, embedding, created_at, doc_path, doc_hash, chunk_hash)

    NOTE:
      - API/프론트에서 "file_path"로 기대하는 경우가 많아서,
        DB의 doc_path를 file_path로 alias 한다.
    """
    
    sql = """
    SELECT  id,
            content,
            doc_title,
            page,
            -- START: DB 스키마 반영 (rag_chunks에는 file_path가 없고 doc_path가 있다)
            doc_path AS file_path,
            -- END: DB 스키마 반영
           1 - (embedding <=> %s::vector) AS score
    FROM rag_chunks
    WHERE doc_group = %s
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (query_vec, doc_group, query_vec, top_k))
            rows = cur.fetchall()

    results = []
    for r in rows:
        results.append({
            "id": str(r[0]),
            "content": r[1],
            "doc_title": r[2],
            "page": r[3],
            "file_path": r[4],
            "score": float(r[5]) if r[5] is not None else 0.0
        })
    return results

def build_context(chunks: list[dict], max_chars: int = 6000) -> str:
    buf = []
    total = 0
    for c in chunks:
        header = f"[{c['doc_title']} p.{c.get('page')}]"
        piece = f"{header}\n{c['content']}\n"
        if total + len(piece) > max_chars:
            break
        buf.append(piece)
        total += len(piece)
    return "\n---\n".join(buf)
