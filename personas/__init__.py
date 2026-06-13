"""
Phase 2 — Reviewer Persona stubs.
Each persona extends ReviewerAgent with a specialised system perspective.
Full implementation in a future release.
"""
from .reviewer_personas import (
    PERSONA_REGISTRY,
    get_persona_system_prompt,
    list_personas,
    RiskManagerPersona,
    InternalAuditorPersona,
    ComplianceOfficerPersona,
    CyberSecurityExpertPersona,
    DataAnalystPersona,
    ProcessExcellenceExpertPersona,
    FraudInvestigatorPersona,
    BusinessContinuitySpecialistPersona,
    AIGovernanceExpertPersona,
    IndustrySMEPersona,
)

__all__ = [
    "PERSONA_REGISTRY",
    "get_persona_system_prompt",
    "list_personas",
    "RiskManagerPersona",
    "InternalAuditorPersona",
    "ComplianceOfficerPersona",
    "CyberSecurityExpertPersona",
    "DataAnalystPersona",
    "ProcessExcellenceExpertPersona",
    "FraudInvestigatorPersona",
    "BusinessContinuitySpecialistPersona",
    "AIGovernanceExpertPersona",
    "IndustrySMEPersona",
]
