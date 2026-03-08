from app.enrichment.engine import EnrichmentEngine
from app.extraction.engine import ExtractionEngine
from app.orchestrator.service import PipelineOrchestrator
from app.outreach.engine import OutreachEngine
from app.scoring.engine import ScoringEngine
from app.semantic.engine import SemanticEngine
from app.sources.engine import SourceEngine
from app.vector.engine import VectorEngine


def build_orchestrator() -> PipelineOrchestrator:
    return PipelineOrchestrator(
        source_engine=SourceEngine(),
        extraction_engine=ExtractionEngine(),
        semantic_engine=SemanticEngine(),
        vector_engine=VectorEngine(),
        enrichment_engine=EnrichmentEngine(),
        scoring_engine=ScoringEngine(),
        outreach_engine=OutreachEngine(),
    )
