from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.embedding import Embedding


class VectorEngine:
    def upsert_embedding(self, db: Session, job_id: int, vector: list[float]) -> None:
        existing = db.get(Embedding, job_id)
        if existing:
            existing.embedding_vector = vector
        else:
            db.add(Embedding(job_id=job_id, embedding_vector=vector))

    def get_embedding(self, db: Session, job_id: int) -> list[float] | None:
        stmt = select(Embedding.embedding_vector).where(Embedding.job_id == job_id)
        return db.execute(stmt).scalar_one_or_none()

    def find_similar_job_ids(
        self,
        db: Session,
        job_id: int,
        limit: int = 10,
    ) -> list[tuple[int, float]]:
        query_embedding = self.get_embedding(db, job_id)
        if query_embedding is None:
            return []

        vector_literal = "[" + ",".join(f"{value:.8f}" for value in query_embedding) + "]"
        stmt = text(
            """
            SELECT j.id AS job_id,
                   (1 - (e.embedding_vector <=> CAST(:query_embedding AS vector))) AS similarity
            FROM jobs j
            JOIN embeddings e ON e.job_id = j.id
            WHERE j.id != :job_id
            ORDER BY e.embedding_vector <-> CAST(:query_embedding AS vector)
            LIMIT :limit
            """
        )
        result = db.execute(
            stmt,
            {"query_embedding": vector_literal, "job_id": job_id, "limit": limit},
        )
        return [(row.job_id, float(row.similarity)) for row in result]
