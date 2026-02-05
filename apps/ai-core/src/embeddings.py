from sentence_transformers import SentenceTransformer
import numpy as np
from settings import settings

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model_name)
    return _model

def embed_query(text: str) -> list[float]:
    model = get_model()
    vec = model.encode([text], normalize_embeddings=True)[0]
    return vec.astype(np.float32).tolist()
