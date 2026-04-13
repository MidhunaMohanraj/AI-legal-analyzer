"""
legal_engine.py — AI Legal Document Analyzer Core
Analyzes contracts, NDAs, terms of service, employment agreements, leases
using Gemini AI to extract:
  - Risk assessment (red flags, dangerous clauses)
  - Plain English summaries of complex legal text
  - Key obligations and deadlines
  - Missing standard clauses
  - Negotiation recommendations
  - Party-specific impact analysis
"""

import json
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
import google.generativeai as genai

# ── Document types ─────────────────────────────────────────────────────────────
DOCUMENT_TYPES = {
    "nda":          "Non-Disclosure Agreement (NDA)",
    "employment":   "Employment Contract",
    "lease":        "Lease / Rental Agreement",
    "service":      "Service Agreement / SaaS Contract",
    "tos":          "Terms of Service / Privacy Policy",
    "partnership":  "Partnership Agreement",
    "ip":           "Intellectual Property Assignment",
    "settlement":   "Settlement Agreement",
    "loan":         "Loan / Credit Agreement",
    "purchase":     "Purchase / Sales Agreement",
    "general":      "General Contract",
}

# ── Risk levels ────────────────────────────────────────────────────────────────
RISK_LEVELS = {
    "critical": {"color": "#dc2626", "emoji": "🚨", "label": "Critical Risk"},
    "high":     {"color": "#f97316", "emoji": "⚠️",  "label": "High Risk"},
    "medium":   {"color": "#eab308", "emoji": "⚡",  "label": "Medium Risk"},
    "low":      {"color": "#22c55e", "emoji": "✅",  "label": "Low Risk"},
    "info":     {"color": "#60a5fa", "emoji": "ℹ️",  "label": "Information"},
}

# ── Common dangerous clauses to watch for ─────────────────────────────────────
DANGEROUS_PATTERNS = [
    "unilateral modification",
    "waive.*right",
    "indemnif",
    "unlimited liability",
    "perpetual.*irrevocable",
    "assign.*without.*consent",
    "automatic.*renewal",
    "liquidated damages",
    "non-compete",
    "work for hire",
    "all intellectual property",
    "sole discretion",
    "no.*warranty",
    "as.is",
    "class action waiver",
    "mandatory arbitration",
    "personal guarantee",
    "joint.*several",
]


# ── Data structures ────────────────────────────────────────────────────────────
@dataclass
class RiskFlag:
    severity:    str           # critical / high / medium / low / info
    category:    str           # e.g. "Liability", "IP Rights", "Termination"
    clause_text: str           # the actual clause (truncated)
    explanation: str           # plain English explanation of the risk
    recommendation: str        # what to do about it
    line_hint:   str           # approximate location in document


@dataclass
class KeyClause:
    clause_type:  str          # e.g. "Termination", "Payment", "Non-Compete"
    original_text: str         # original legal text
    plain_english: str         # plain English translation
    is_standard:  bool         # is this a standard clause?
    favorable_to: str          # "party_a" / "party_b" / "balanced" / "unclear"


@dataclass
class Obligation:
    party:      str            # who must do this
    action:     str            # what they must do
    deadline:   str            # when (if specified)
    consequence: str           # what happens if not done


@dataclass
class LegalAnalysis:
    # Document metadata
    doc_type:        str
    doc_type_label:  str
    detected_parties: list[str]
    governing_law:   str
    effective_date:  str
    word_count:      int
    analyzed_at:     str = field(default_factory=lambda: datetime.now().isoformat())

    # Core analysis
    executive_summary: str     # 3-4 sentence plain English overview
    overall_risk:      str     # critical / high / medium / low
    risk_score:        int     # 0-100 (100 = most risky)
    risk_flags:        list[RiskFlag] = field(default_factory=list)
    key_clauses:       list[KeyClause] = field(default_factory=list)
    obligations:       list[Obligation] = field(default_factory=list)

    # Structural analysis
    missing_clauses:   list[str] = field(default_factory=list)
    unusual_clauses:   list[str] = field(default_factory=list)
    standard_clauses:  list[str] = field(default_factory=list)

    # Recommendations
    negotiation_points: list[str] = field(default_factory=list)
    red_lines:          list[str] = field(default_factory=list)  # must-change items
    quick_wins:         list[str] = field(default_factory=list)  # easy improvements

    # Party-specific
    favorable_clauses:   list[str] = field(default_factory=list)
    unfavorable_clauses: list[str] = field(default_factory=list)

    # Disclaimer
    disclaimer: str = "This analysis is for informational purposes only and does not constitute legal advice. Always consult a qualified attorney for legal matters."


# ── Gemini analysis ────────────────────────────────────────────────────────────
def detect_document_type(text: str, api_key: str) -> tuple[str, list[str]]:
    """Detect document type and parties from text."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.1, "max_output_tokens": 200},
    )
    sample = text[:1500]
    prompt = f"""Analyze this legal document excerpt and return JSON only:
{{
  "doc_type": "<one of: nda|employment|lease|service|tos|partnership|ip|settlement|loan|purchase|general>",
  "parties": ["Party 1 name or role", "Party 2 name or role"],
  "governing_law": "<state/country of governing law or 'Not specified'>",
  "effective_date": "<date or 'Not specified'>"
}}

DOCUMENT:
{sample}"""
    try:
        r   = model.generate_content(prompt)
        raw = re.sub(r"^```json\s*|^```\s*|\s*```$", "", r.text.strip(), flags=re.MULTILINE)
        d   = json.loads(raw)
        return d.get("doc_type", "general"), d.get("parties", ["Party A", "Party B"]), \
               d.get("governing_law", "Not specified"), d.get("effective_date", "Not specified")
    except Exception:
        return "general", ["Party A", "Party B"], "Not specified", "Not specified"


def analyze_risks(text: str, doc_type: str, api_key: str) -> list[RiskFlag]:
    """Extract all risk flags from the document."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.1, "max_output_tokens": 2000},
    )

    # Process in chunks for long documents
    chunk = text[:6000]

    prompt = f"""You are an expert contract attorney. Identify ALL risk flags in this {DOCUMENT_TYPES.get(doc_type, 'contract')}.

DOCUMENT:
{chunk}

Return JSON array of risk flags (find at least 5, up to 12):
[
  {{
    "severity": "<critical|high|medium|low|info>",
    "category": "<Liability|IP Rights|Termination|Payment|Privacy|Non-Compete|Arbitration|Auto-Renewal|Indemnification|Assignment|Warranty|Data|Other>",
    "clause_text": "<exact or paraphrased clause, max 100 chars>",
    "explanation": "<plain English: why is this risky? 1-2 sentences>",
    "recommendation": "<specific action to take: 1 sentence>",
    "line_hint": "<approximate location: 'Section 3', 'Near the end', 'First paragraph', etc.>"
  }}
]

Severity guide:
- critical: Could result in serious legal/financial harm, must be changed
- high: Significantly unfavorable, strongly recommend negotiating
- medium: Worth discussing but not deal-breaking
- low: Minor issue or standard clause worth noting
- info: Neutral information that's important to know

Return ONLY the JSON array."""

    try:
        r    = model.generate_content(prompt)
        raw  = re.sub(r"^```json\s*|^```\s*|\s*```$", "", r.text.strip(), flags=re.MULTILINE)
        data = json.loads(raw)
        return [RiskFlag(**item) for item in data if isinstance(item, dict)]
    except Exception:
        return [RiskFlag(
            severity="info",
            category="Analysis",
            clause_text="Unable to parse",
            explanation="Risk analysis could not be completed for this section.",
            recommendation="Review manually.",
            line_hint="Unknown",
        )]


def analyze_clauses(text: str, doc_type: str, api_key: str) -> list[KeyClause]:
    """Extract and translate key clauses."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.15, "max_output_tokens": 2000},
    )
    chunk = text[:5000]
    prompt = f"""Extract the 6-8 most important clauses from this {DOCUMENT_TYPES.get(doc_type, 'contract')}.

DOCUMENT:
{chunk}

Return JSON array:
[
  {{
    "clause_type": "<e.g. Termination, Payment Terms, Non-Compete, Confidentiality, IP Assignment, Liability Cap, Governing Law>",
    "original_text": "<the actual clause text, max 150 chars>",
    "plain_english": "<explain in simple terms what this means for a non-lawyer, 1-2 sentences>",
    "is_standard": <true if this is a standard/common clause, false if unusual>,
    "favorable_to": "<party_a|party_b|balanced|unclear>"
  }}
]

Return ONLY the JSON array."""
    try:
        r    = model.generate_content(prompt)
        raw  = re.sub(r"^```json\s*|^```\s*|\s*```$", "", r.text.strip(), flags=re.MULTILINE)
        data = json.loads(raw)
        return [KeyClause(**item) for item in data if isinstance(item, dict)]
    except Exception:
        return []


def analyze_obligations(text: str, doc_type: str, parties: list[str], api_key: str) -> list[Obligation]:
    """Extract all obligations and deadlines."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.1, "max_output_tokens": 1500},
    )
    chunk = text[:4000]
    prompt = f"""Extract all obligations (things parties MUST do) from this contract.
Parties: {', '.join(parties)}

DOCUMENT:
{chunk}

Return JSON array (find 5-10 obligations):
[
  {{
    "party": "<which party or 'Both parties'>",
    "action": "<what they must do, plain English>",
    "deadline": "<when, or 'No deadline specified' or 'Ongoing'>",
    "consequence": "<what happens if not done, or 'Not specified'>"
  }}
]

Return ONLY the JSON array."""
    try:
        r    = model.generate_content(prompt)
        raw  = re.sub(r"^```json\s*|^```\s*|\s*```$", "", r.text.strip(), flags=re.MULTILINE)
        data = json.loads(raw)
        return [Obligation(**item) for item in data if isinstance(item, dict)]
    except Exception:
        return []


def generate_summary_and_recommendations(
    text: str, doc_type: str, parties: list[str],
    risk_flags: list[RiskFlag], api_key: str,
) -> dict:
    """Generate executive summary, recommendations, and missing clauses."""
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        "gemini-1.5-flash",
        generation_config={"temperature": 0.2, "max_output_tokens": 1500},
    )
    flags_summary = "\n".join([
        f"- [{f.severity.upper()}] {f.category}: {f.explanation}"
        for f in risk_flags[:8]
    ])
    chunk = text[:3000]
    prompt = f"""You are a senior contract attorney. Based on this {DOCUMENT_TYPES.get(doc_type, 'contract')} analysis:

DOCUMENT EXCERPT:
{chunk}

RISKS IDENTIFIED:
{flags_summary}

Return JSON:
{{
  "executive_summary": "<3-4 sentence plain English overview: what is this document, who are the parties, what does it do, and what's the overall risk level>",
  "overall_risk": "<critical|high|medium|low>",
  "risk_score": <0-100 integer, 100 = most risky>,
  "missing_clauses": ["<important clause missing from this document>", ...],
  "unusual_clauses": ["<clause that is unusual or non-standard>", ...],
  "standard_clauses": ["<standard clauses that ARE present>", ...],
  "negotiation_points": ["<specific negotiation recommendation>", ...],
  "red_lines": ["<must-change before signing>", ...],
  "quick_wins": ["<easy change that would significantly improve the document>", ...],
  "favorable_clauses": ["<clause favorable to the reviewer/weaker party>", ...],
  "unfavorable_clauses": ["<clause unfavorable to the reviewer/weaker party>", ...]
}}

Be specific. Use plain English. Focus on protecting the reviewer's interests.
Return ONLY the JSON."""
    try:
        r    = model.generate_content(prompt)
        raw  = re.sub(r"^```json\s*|^```\s*|\s*```$", "", r.text.strip(), flags=re.MULTILINE)
        return json.loads(raw)
    except Exception:
        return {
            "executive_summary": "Analysis complete. Review the risk flags below for details.",
            "overall_risk": "medium",
            "risk_score": 50,
            "missing_clauses": [],
            "unusual_clauses": [],
            "standard_clauses": [],
            "negotiation_points": [],
            "red_lines": [],
            "quick_wins": [],
            "favorable_clauses": [],
            "unfavorable_clauses": [],
        }


# ── Main analysis function ─────────────────────────────────────────────────────
def analyze_document(
    text: str,
    api_key: str,
    doc_type_override: str = "auto",
    on_progress: callable = None,
) -> LegalAnalysis:
    """
    Run full legal analysis on a document.
    Calls on_progress(step, total, message) for streaming UI updates.
    """
    steps = 5
    word_count = len(text.split())

    def progress(step, msg):
        if on_progress:
            on_progress(step, steps, msg)

    # Step 1: Detect document type
    progress(1, "🔍 Detecting document type and parties...")
    if doc_type_override == "auto":
        doc_type, parties, governing_law, effective_date = detect_document_type(text, api_key)
    else:
        doc_type = doc_type_override
        _, parties, governing_law, effective_date = detect_document_type(text, api_key)

    # Step 2: Risk analysis
    progress(2, "⚠️ Analysing risks and red flags...")
    risk_flags = analyze_risks(text, doc_type, api_key)

    # Step 3: Clause analysis
    progress(3, "📋 Extracting and translating key clauses...")
    key_clauses = analyze_clauses(text, doc_type, api_key)

    # Step 4: Obligations
    progress(4, "📌 Identifying obligations and deadlines...")
    obligations = analyze_obligations(text, doc_type, parties, api_key)

    # Step 5: Summary + recommendations
    progress(5, "📝 Generating summary and recommendations...")
    summary_data = generate_summary_and_recommendations(
        text, doc_type, parties, risk_flags, api_key
    )

    return LegalAnalysis(
        doc_type=doc_type,
        doc_type_label=DOCUMENT_TYPES.get(doc_type, "General Contract"),
        detected_parties=parties,
        governing_law=governing_law,
        effective_date=effective_date,
        word_count=word_count,
        executive_summary=summary_data.get("executive_summary", ""),
        overall_risk=summary_data.get("overall_risk", "medium"),
        risk_score=int(summary_data.get("risk_score", 50)),
        risk_flags=risk_flags,
        key_clauses=key_clauses,
        obligations=obligations,
        missing_clauses=summary_data.get("missing_clauses", []),
        unusual_clauses=summary_data.get("unusual_clauses", []),
        standard_clauses=summary_data.get("standard_clauses", []),
        negotiation_points=summary_data.get("negotiation_points", []),
        red_lines=summary_data.get("red_lines", []),
        quick_wins=summary_data.get("quick_wins", []),
        favorable_clauses=summary_data.get("favorable_clauses", []),
        unfavorable_clauses=summary_data.get("unfavorable_clauses", []),
    )


# ── Sample documents for testing ───────────────────────────────────────────────
SAMPLE_NDA = """NON-DISCLOSURE AGREEMENT

This Non-Disclosure Agreement ("Agreement") is entered into as of January 1, 2025, between TechCorp Inc., a Delaware corporation ("Disclosing Party"), and John Smith, an individual ("Receiving Party").

1. CONFIDENTIAL INFORMATION
The Receiving Party agrees to hold in strict confidence all information disclosed by the Disclosing Party, including but not limited to trade secrets, business plans, financial data, technical specifications, and customer lists (collectively "Confidential Information"). This obligation shall survive termination of this Agreement for a period of ten (10) years.

2. NON-COMPETE
The Receiving Party agrees not to engage in any business that competes directly or indirectly with the Disclosing Party for a period of five (5) years within the United States. The Receiving Party further agrees not to solicit any employees or customers of the Disclosing Party during this period.

3. INTELLECTUAL PROPERTY
Any work product, inventions, or improvements created by the Receiving Party, whether or not using Confidential Information, shall be the sole and exclusive property of the Disclosing Party. The Receiving Party irrevocably assigns all intellectual property rights to the Disclosing Party.

4. REMEDIES
The Receiving Party acknowledges that breach of this Agreement would cause irreparable harm to the Disclosing Party. The Disclosing Party shall be entitled to seek injunctive relief and liquidated damages of $500,000 per breach, in addition to all other remedies available at law or equity. The Receiving Party waives any right to a jury trial.

5. INDEMNIFICATION
The Receiving Party shall indemnify, defend, and hold harmless the Disclosing Party from any and all claims, damages, losses, costs, and expenses (including reasonable attorneys' fees) arising from or related to any breach of this Agreement.

6. MODIFICATION
The Disclosing Party reserves the right to modify this Agreement at any time without prior notice to the Receiving Party. Continued use of Confidential Information shall constitute acceptance of any modifications.

7. GOVERNING LAW
This Agreement shall be governed by the laws of Delaware. Any disputes shall be resolved through binding arbitration. Class action lawsuits are expressly waived.

8. SEVERABILITY
If any provision of this Agreement is found to be unenforceable, the remaining provisions shall remain in full force and effect.

IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above."""

SAMPLE_EMPLOYMENT = """EMPLOYMENT AGREEMENT

This Employment Agreement is made between StartupXYZ Inc. ("Company") and the undersigned employee ("Employee").

1. POSITION AND DUTIES
Employee agrees to serve as Software Engineer and perform all duties as assigned by the Company. Employee agrees to work such hours as required to complete assigned duties, with no additional compensation for overtime.

2. COMPENSATION
Base salary of $80,000 per year, payable bi-weekly. The Company may adjust compensation at its sole discretion with 30 days notice.

3. AT-WILL EMPLOYMENT
This is an at-will employment relationship. The Company may terminate this agreement at any time, for any reason or no reason, with or without cause, and with or without notice.

4. INTELLECTUAL PROPERTY
All inventions, works of authorship, and developments created by Employee, whether during or outside working hours, whether or not using Company resources, shall be the exclusive property of the Company. Employee hereby assigns all such rights to the Company.

5. NON-COMPETE
For two (2) years following termination, Employee shall not work for any company that provides services similar to those of the Company within the United States.

6. CONFIDENTIALITY
Employee shall maintain strict confidentiality of all Company information indefinitely, even after termination.

7. ARBITRATION
All disputes shall be resolved by binding arbitration. Employee waives the right to participate in class action lawsuits.

SIGNED: ______________________"""
