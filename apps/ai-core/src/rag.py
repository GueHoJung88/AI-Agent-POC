import time
from typing import Any
from db import get_conn

def retrieve_pgvector(query_vec: list[float], doc_group: str, top_k: int) -> list[dict[str, Any]]:
    """
    cosine distance: embedding <=> query_vec
    score = 1 - distance
    """
    sql = """
    SELECT id, content, doc_title, page, file_path,
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
