from functools import cached_property

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import Settings, get_settings


class SemanticEngine:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @cached_property
    def model(self) -> SentenceTransformer:
        return SentenceTransformer(self.settings.embedding_model)

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(
            texts,
            batch_size=self.settings.embedding_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [embedding.tolist() for embedding in embeddings]

    def cosine_similarity(self, left: list[float], right: list[float]) -> float:
        left_vec = np.array(left)
        right_vec = np.array(right)
        denom = np.linalg.norm(left_vec) * np.linalg.norm(right_vec)
        if denom == 0:
            return 0.0
        return float(np.dot(left_vec, right_vec) / denom)

    def score_job(self, job_description: str, user_profile: str) -> tuple[float, list[float]]:
        job_embedding, profile_embedding = self.embed_texts([job_description, user_profile])
        score = self.cosine_similarity(job_embedding, profile_embedding)
        return score, job_embedding
