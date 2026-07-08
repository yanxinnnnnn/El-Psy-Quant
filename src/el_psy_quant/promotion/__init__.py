"""Research-to-paper promotion boundaries."""

from el_psy_quant.promotion.candidates import (
    PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION,
    PaperPromotionCandidate,
    create_paper_promotion_candidate,
)
from el_psy_quant.promotion.evidence import (
    PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION,
    PromotionEvidenceSummary,
    create_promotion_evidence_summary,
)
from el_psy_quant.promotion.source_references import (
    PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION,
    SUPPORTED_PROMOTION_SOURCE_TYPES,
    PromotionSourceReference,
    create_promotion_source_reference,
)

__all__ = [
    "PAPER_PROMOTION_CANDIDATE_SCHEMA_VERSION",
    "PROMOTION_EVIDENCE_SUMMARY_SCHEMA_VERSION",
    "PROMOTION_SOURCE_REFERENCE_SCHEMA_VERSION",
    "SUPPORTED_PROMOTION_SOURCE_TYPES",
    "PaperPromotionCandidate",
    "PromotionEvidenceSummary",
    "PromotionSourceReference",
    "create_paper_promotion_candidate",
    "create_promotion_evidence_summary",
    "create_promotion_source_reference",
]
