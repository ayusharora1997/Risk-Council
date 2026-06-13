"""
Phase 2 — Reviewer Persona stubs.

Each class represents a specialised reviewer role that will, in a future release,
inject a role-specific system prompt into the ReviewerAgent to produce
domain-expert feedback (e.g. a Fraud Investigator looks for fraud-enablement gaps;
a Cyber Security Expert focuses on data security controls).

CURRENT STATUS: Interface + system-prompt stubs only.
Full implementation (domain-specific scoring rubrics, persona chains) is deferred.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from models.schemas import PolicyDocument, ReviewerFeedback


# ---------------------------------------------------------------------------
# Base persona interface
# ---------------------------------------------------------------------------

class BaseReviewerPersona(ABC):
    """Interface every reviewer persona must implement."""

    name: str = "Generic Reviewer"
    description: str = "Base reviewer persona — not intended for direct use."

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Return the persona-specific system prompt injected into the LLM call."""

    def pre_process(self, policy: PolicyDocument) -> PolicyDocument:
        """Optional pre-processing hook before the policy is sent to the LLM."""
        return policy  # default: pass-through

    def post_process(self, feedback: ReviewerFeedback) -> ReviewerFeedback:
        """Optional post-processing hook to enrich or reweight the raw feedback."""
        return feedback  # default: pass-through

    # TODO Phase 2: add domain-specific scoring rubric overrides
    # TODO Phase 2: add structured domain checklists
    # TODO Phase 2: integrate with industry standard frameworks (NIST, ISO 27001, COBIT)


# ---------------------------------------------------------------------------
# Concrete persona stubs
# ---------------------------------------------------------------------------

class RiskManagerPersona(BaseReviewerPersona):
    """Focuses on enterprise risk identification, rating, and appetite alignment."""

    name = "Risk Manager"
    description = (
        "Evaluates the policy through an enterprise risk lens: risk appetite alignment, "
        "residual risk, risk register integration, and escalation paths."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Chief Risk Officer reviewing this policy from an enterprise risk management "
            "perspective. Focus on: risk identification completeness, alignment with the organisation's "
            "risk appetite, residual risk after controls, escalation and reporting paths, and "
            "integration with the enterprise risk register. "
            "Apply COSO ERM and ISO 31000 frameworks where appropriate."
        )
    # TODO Phase 2: map findings to ISO 31000 risk categories


class InternalAuditorPersona(BaseReviewerPersona):
    """Evaluates auditability, evidence requirements, and control testability."""

    name = "Internal Auditor"
    description = (
        "Reviews for auditability: are controls testable, is evidence defined, "
        "are roles accountable, and can the policy be independently verified?"
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Head of Internal Audit reviewing this policy for auditability. "
            "Focus on: whether controls are measurable and testable, whether evidence "
            "requirements are defined, segregation of duties, audit trail provisions, "
            "and alignment with IIA Standards. Flag anything that cannot be independently verified."
        )
    # TODO Phase 2: generate an auditability scorecard per control


class ComplianceOfficerPersona(BaseReviewerPersona):
    """Maps policy provisions against applicable regulations and standards."""

    name = "Compliance Officer"
    description = (
        "Checks regulatory coverage: GDPR, SOX, DORA, AI Act, ISO 27001, and "
        "other applicable frameworks depending on the policy domain."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Chief Compliance Officer reviewing this policy for regulatory alignment. "
            "Identify gaps against relevant regulations (GDPR, AI Act, SOX, DORA, CCPA, ISO 27001, "
            "NIST CSF) as applicable. Flag missing mandatory disclosures, undefined data retention "
            "periods, absent subject rights provisions, and unaddressed breach notification requirements."
        )
    # TODO Phase 2: auto-detect applicable regulations from scenario keywords


class CyberSecurityExpertPersona(BaseReviewerPersona):
    """Reviews cybersecurity controls, data security, and threat modelling."""

    name = "Cyber Security Expert"
    description = (
        "Assesses data security controls, access management, encryption requirements, "
        "incident response, and alignment with NIST CSF / CIS Controls."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a CISO reviewing this policy for cybersecurity adequacy. "
            "Evaluate: access control and least privilege, encryption at rest and in transit, "
            "vulnerability management, penetration testing requirements, security monitoring, "
            "incident response integration, and alignment with NIST CSF, CIS Controls v8, "
            "and ISO 27001 Annex A. Identify every security control gap."
        )
    # TODO Phase 2: map gaps to MITRE ATT&CK techniques


class DataAnalystPersona(BaseReviewerPersona):
    """Focuses on data quality, analytics governance, and metrics definition."""

    name = "Data Analyst"
    description = (
        "Reviews data governance provisions: data quality standards, KPI definitions, "
        "reporting cadence, and analytics bias risks."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Senior Data Governance Analyst reviewing this policy. "
            "Focus on: data quality standards and thresholds, defined KPIs and metrics, "
            "data lineage and provenance requirements, analytics bias risks, "
            "reporting and dashboard requirements, and data retention / archival policies. "
            "Flag undefined metrics, missing data quality gates, and analytics blind spots."
        )
    # TODO Phase 2: generate a data quality scorecard


class ProcessExcellenceExpertPersona(BaseReviewerPersona):
    """Assesses operational efficiency, process design, and continuous improvement."""

    name = "Process Excellence Expert"
    description = (
        "Evaluates process clarity, efficiency, automation opportunities, "
        "and alignment with Lean / Six Sigma principles."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Process Excellence / Lean Six Sigma Black Belt reviewing this policy. "
            "Assess: clarity and unambiguity of procedures, elimination of waste and redundant steps, "
            "automation and digitisation opportunities, handoff and escalation clarity, "
            "continuous improvement (PDCA) mechanisms, and measurable process KPIs. "
            "Identify bottlenecks, ambiguous handoffs, and missing process owners."
        )
    # TODO Phase 2: produce a SIPOC and RACI gap analysis


class FraudInvestigatorPersona(BaseReviewerPersona):
    """Identifies fraud enablement gaps, detection controls, and investigation procedures."""

    name = "Fraud Investigator"
    description = (
        "Reviews the policy for fraud risk exposure: segregation of duties, "
        "anomaly detection, whistleblower provisions, and investigation protocols."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Certified Fraud Examiner (CFE) reviewing this policy for fraud exposure. "
            "Identify: gaps in segregation of duties that create fraud opportunity, "
            "missing anomaly detection controls, absence of whistleblower / speak-up mechanisms, "
            "undefined fraud investigation procedures, collusion scenarios, and "
            "third-party fraud vectors. Apply the ACFE Fraud Triangle framework."
        )
    # TODO Phase 2: map risks to ACFE fraud tree


class BusinessContinuitySpecialistPersona(BaseReviewerPersona):
    """Evaluates BCP/DR provisions, RTO/RPO definitions, and resilience design."""

    name = "Business Continuity Specialist"
    description = (
        "Reviews for operational resilience: BCP triggers, RTO/RPO targets, "
        "failover procedures, and third-party dependency risk."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are a Business Continuity and Resilience Manager reviewing this policy. "
            "Evaluate: BCP trigger criteria, RTO and RPO definitions, tested failover procedures, "
            "single points of failure, third-party and supplier dependency risks, "
            "crisis communication protocols, and alignment with ISO 22301. "
            "Flag missing recovery time objectives and untested contingency scenarios."
        )
    # TODO Phase 2: generate BIA (Business Impact Analysis) checklist


class AIGovernanceExpertPersona(BaseReviewerPersona):
    """Specialises in AI-specific risks: model bias, explainability, and lifecycle governance."""

    name = "AI Governance Expert"
    description = (
        "Reviews AI-specific provisions: model risk, algorithmic bias, explainability, "
        "human oversight, and EU AI Act / NIST AI RMF alignment."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are an AI Governance and Ethics expert reviewing this policy through the lens of "
            "responsible AI. Evaluate: algorithmic bias mitigation measures, model explainability and "
            "transparency requirements, human-in-the-loop provisions, model lifecycle governance "
            "(development, testing, deployment, retirement), EU AI Act risk classification alignment, "
            "NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE) coverage, and fairness across protected "
            "characteristics. Flag every missing AI-specific control."
        )
    # TODO Phase 2: auto-classify AI system risk tier per EU AI Act Annex III


class IndustrySMEPersona(BaseReviewerPersona):
    """Domain Subject Matter Expert — reviews for industry-specific fit and terminology."""

    name = "Industry SME"
    description = (
        "Evaluates whether the policy is fit-for-purpose in the target industry, "
        "using domain-specific standards and terminology. Industry is inferred from context."
    )

    @property
    def system_prompt(self) -> str:
        return (
            "You are an industry Subject Matter Expert reviewing this policy for sector-specific "
            "fit and completeness. Identify terminology mismatches, missing industry-standard "
            "controls (e.g. PCI-DSS for payments, HIPAA for healthcare, MiFID II for financial "
            "services), regulatory body-specific requirements, and practical implementation gaps "
            "that a practitioner in this industry would immediately notice. "
            "Infer the target industry from the policy content."
        )
    # TODO Phase 2: accept explicit industry parameter and load sector-specific ruleset


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PERSONA_REGISTRY: Dict[str, type[BaseReviewerPersona]] = {
    "risk_manager": RiskManagerPersona,
    "internal_auditor": InternalAuditorPersona,
    "compliance_officer": ComplianceOfficerPersona,
    "cyber_security_expert": CyberSecurityExpertPersona,
    "data_analyst": DataAnalystPersona,
    "process_excellence_expert": ProcessExcellenceExpertPersona,
    "fraud_investigator": FraudInvestigatorPersona,
    "business_continuity_specialist": BusinessContinuitySpecialistPersona,
    "ai_governance_expert": AIGovernanceExpertPersona,
    "industry_sme": IndustrySMEPersona,
}


def list_personas() -> List[str]:
    """Return all registered persona keys."""
    return list(PERSONA_REGISTRY.keys())


def get_persona_system_prompt(persona_key: str) -> Optional[str]:
    """Return the system prompt for a given persona key, or None if not found."""
    cls = PERSONA_REGISTRY.get(persona_key)
    if cls is None:
        return None
    return cls().system_prompt
