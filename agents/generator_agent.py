"""
GeneratorAgent — creates the initial document and refines it after each reviewer pass.
Supports document types: policy, sop, workflow.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from models.schemas import PolicyDocument, ReviewerFeedback
from providers.base_provider import BaseProvider

# ── System prompts ─────────────────────────────────────────────────────────────

_SYSTEM_POLICY = """You are a senior GRC (Governance, Risk & Compliance) architect and policy writer.
Your expertise spans AI governance, regulatory compliance, risk management, and internal controls.

When writing policy documents:
- Use clear, precise, unambiguous language appropriate for enterprise use.
- Structure every document with numbered sections and sub-sections.
- Define all key terms.
- Assign explicit roles and responsibilities.
- Include measurable controls with specific thresholds or frequencies.
- Consider fairness, bias, ethical soundness, and practical implementability.
- Do NOT use placeholders such as [TBD] or [INSERT NAME].
"""

_SYSTEM_SOP = """You are a senior Business Process and Operations Excellence specialist.
Your expertise spans ISO 9001, Six Sigma, Lean operations, and procedural documentation.

When writing Standard Operating Procedures:
- Use clear, action-oriented imperative language.
- Break procedures into precise, numbered steps a new employee can follow.
- Define responsibilities explicitly for each step.
- Include decision checkpoints, quality gates, and exception paths.
- Specify tools, systems, templates, and record-keeping requirements.
- Do NOT use placeholders such as [TBD] or [INSERT NAME].
"""

_SYSTEM_WORKFLOW = """You are a senior Business Architect and Process Design specialist.
Your expertise spans BPM, BPMN notation, workflow automation, and process optimisation.

When designing workflow documents:
- Define clear triggers, inputs, process steps, decision points, and outputs.
- Assign swim-lane ownership for each activity.
- Specify integration points with other systems or teams.
- Include exception paths, escalation routes, and SLAs.
- Define measurable KPIs for the workflow.
- Do NOT use placeholders such as [TBD] or [INSERT NAME].
"""

# ── Initial prompt templates ───────────────────────────────────────────────────

_POLICY_INITIAL = """Create a comprehensive enterprise Policy document for the following scenario:

SCENARIO:
{scenario}
{reference_section}
The document MUST include all of the following sections:

1. Executive Summary
2. Purpose and Objectives
3. Scope and Applicability
4. Definitions and Key Terms
5. Policy Statement
6. Roles and Responsibilities (RACI if applicable)
7. Controls and Safeguards
   7.1 Preventive Controls
   7.2 Detective Controls
   7.3 Corrective Controls
8. Compliance and Regulatory Requirements
9. Monitoring, Reporting, and Audit Procedures
10. Incident and Exception Management
11. Enforcement and Consequences
12. Training and Awareness Requirements
13. Document Review and Update Cycle
14. Appendices (as needed)

Write the complete document now. Be specific, thorough, and enterprise-ready.
"""

_SOP_INITIAL = """Create a comprehensive Standard Operating Procedure (SOP) for the following scenario:

SCENARIO:
{scenario}
{reference_section}
The SOP MUST include all of the following sections:

1. Document Header (Title, Version, Owner, Effective Date, Review Date, Approver)
2. Purpose
3. Scope
4. Definitions and Abbreviations
5. Roles and Responsibilities
6. Materials, Tools, and Systems Required
7. Pre-Conditions and Prerequisites
8. Procedure Steps (numbered, detailed, with sub-steps where needed)
   - Include decision points with branching instructions
   - Specify the responsible role for each step
   - Include timing/frequency where applicable
9. Quality Checks and Acceptance Criteria
10. Exception and Error Handling
11. Records and Documentation Requirements
12. Related Documents and References
13. Revision History

Write the complete SOP now. Every step must be specific and actionable.
"""

_WORKFLOW_INITIAL = """Create a comprehensive Workflow Design document for the following scenario:

SCENARIO:
{scenario}
{reference_section}
The Workflow Design MUST include all of the following sections:

1. Workflow Overview (purpose, scope, trigger conditions)
2. Stakeholders and Swim-Lane Owners
3. Process Inputs and Triggers
4. Workflow Steps and Activities
   - For each step: activity name, owner, inputs, outputs, system/tool used
5. Decision Points and Business Rules
6. Exception Paths and Escalation Routes
7. Integration Points (systems, APIs, handoffs to other teams)
8. Outputs and Deliverables
9. SLAs, Timing, and Performance Targets
10. Key Performance Indicators (KPIs) and Metrics
11. Process Controls and Audit Checkpoints
12. Automation Opportunities
13. Appendix: Process Flow Diagram (described textually with BPMN-style notation)

Write the complete Workflow Design now. Be specific about ownership, timing, and integration points.
"""

# ── Improvement prompt (generic — adapts to document type) ────────────────────

_IMPROVEMENT_TEMPLATE = """You previously drafted Version {version} of the following {doc_type_label}:

---BEGIN DOCUMENT V{version}---
{policy_content}
---END DOCUMENT V{version}---

A multi-model review council evaluated the document and provided this aggregated feedback:

AGGREGATE SCORE: {aggregate_score:.1f}/100

IDENTIFIED BIASES:
{biases}

ETHICAL RISKS:
{ethical_risks}

IMPLEMENTATION CHALLENGES:
{implementation_challenges}

MISSING CONTROLS:
{missing_controls}

RECOMMENDATIONS:
{recommendations}

REVIEWER SUMMARIES:
{summaries}

Your task:
- Address EVERY identified issue substantively.
- Strengthen or add controls where gaps were noted.
- Remove or neutralise any identified biases.
- Improve fairness, ethical soundness, and governance provisions.
- Preserve sections that received no critical feedback.
- Do NOT truncate the document — the improved version must be at least as long as the original.

Write the complete improved {doc_type_label} (Version {new_version}) now.
"""

_DOC_TYPE_LABELS = {
    "policy": "Policy Document",
    "sop": "Standard Operating Procedure",
    "workflow": "Workflow Design",
}

_SYSTEM_PROMPTS = {
    "policy": _SYSTEM_POLICY,
    "sop": _SYSTEM_SOP,
    "workflow": _SYSTEM_WORKFLOW,
}

_INITIAL_TEMPLATES = {
    "policy": _POLICY_INITIAL,
    "sop": _SOP_INITIAL,
    "workflow": _WORKFLOW_INITIAL,
}


def _format_list(items: List[str]) -> str:
    if not items:
        return "  (none identified)"
    return "\n".join(f"  - {item}" for item in items)


class GeneratorAgent:
    """Generates and iteratively improves governance documents."""

    def __init__(self, provider: BaseProvider, model: str) -> None:
        self.provider = provider
        self.model = model
        self._version_history: List[PolicyDocument] = []

    def generate_initial(
        self,
        scenario: str,
        document_type: str = "policy",
        reference_content: Optional[str] = None,
    ) -> PolicyDocument:
        """Produce the first version from a scenario string and optional reference."""
        doc_type = document_type if document_type in _INITIAL_TEMPLATES else "policy"

        ref_section = ""
        if reference_content:
            ref_section = (
                "\nREFERENCE DOCUMENT (use this as a basis / input for the document below):\n"
                f"{'─' * 60}\n"
                f"{reference_content[:10000]}\n"
                f"{'─' * 60}\n\n"
            )

        prompt = _INITIAL_TEMPLATES[doc_type].format(
            scenario=scenario,
            reference_section=ref_section,
        )

        content = self.provider.generate(
            prompt=prompt,
            model=self.model,
            system_prompt=_SYSTEM_PROMPTS[doc_type],
            temperature=0.7,
        )
        doc = PolicyDocument(
            version=1,
            content=content,
            generator_model=self.model,
            generator_provider=self.provider.provider_name,
        )
        self._version_history.append(doc)
        return doc

    def improve(
        self,
        current_policy: PolicyDocument,
        aggregated_feedback: Dict[str, Any],
        reviews: Optional[List[ReviewerFeedback]] = None,
        document_type: str = "policy",
    ) -> PolicyDocument:
        """Produce the next improved version using reviewer feedback."""
        doc_type = document_type if document_type in _DOC_TYPE_LABELS else "policy"
        new_version = current_policy.version + 1
        summaries = (
            "\n".join(
                f"  [{r.reviewer_provider}/{r.reviewer_model}]: {r.summary}"
                for r in (reviews or [])
            )
            or "  (no individual summaries)"
        )

        prompt = _IMPROVEMENT_TEMPLATE.format(
            version=current_policy.version,
            new_version=new_version,
            doc_type_label=_DOC_TYPE_LABELS[doc_type],
            policy_content=current_policy.content,
            aggregate_score=aggregated_feedback.get("aggregate_score", 0),
            biases=_format_list(aggregated_feedback.get("biases", [])),
            ethical_risks=_format_list(aggregated_feedback.get("ethical_risks", [])),
            implementation_challenges=_format_list(
                aggregated_feedback.get("implementation_challenges", [])
            ),
            missing_controls=_format_list(aggregated_feedback.get("missing_controls", [])),
            recommendations=_format_list(aggregated_feedback.get("recommendations", [])),
            summaries=summaries,
        )

        content = self.provider.generate(
            prompt=prompt,
            model=self.model,
            system_prompt=_SYSTEM_PROMPTS[doc_type],
            temperature=0.65,
        )

        doc = PolicyDocument(
            version=new_version,
            content=content,
            generator_model=self.model,
            generator_provider=self.provider.provider_name,
        )
        self._version_history.append(doc)
        return doc

    @property
    def version_history(self) -> List[PolicyDocument]:
        return list(self._version_history)

    @property
    def current_version(self) -> int:
        return len(self._version_history)
