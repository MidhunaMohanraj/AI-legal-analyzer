"""
app.py — AI Legal Document Analyzer Dashboard
"""    
    
import sys, json, io
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).parent / "src"))
from legal_engine import (
    DOCUMENT_TYPES, RISK_LEVELS, analyze_document,
    LegalAnalysis, SAMPLE_NDA, SAMPLE_EMPLOYMENT,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Legal Analyzer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Crimson+Text:ital,wght@0,600;1,400&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .main { background: #07080d; }

  .hero {
    background: linear-gradient(135deg,#0a080f 0%,#07080d 55%,#050a08 100%);
    border:1px solid #1a1a30; border-radius:16px;
    padding:34px 40px; text-align:center; margin-bottom:24px;
  }
  .hero h1 { font-size:38px; font-weight:700; color:#fff; margin:0 0 6px; }
  .hero p  { color:#64748b; font-size:14px; margin:0; }

  .risk-critical { background:#150205; border:1px solid #7f1d1d; border-left:4px solid #dc2626; border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0; }
  .risk-high     { background:#150a00; border:1px solid #7c2d12; border-left:4px solid #f97316; border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0; }
  .risk-medium   { background:#14120a; border:1px solid #78350f; border-left:4px solid #eab308; border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0; }
  .risk-low      { background:#051405; border:1px solid #14532d; border-left:4px solid #22c55e; border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0; }
  .risk-info     { background:#050a18; border:1px solid #1e3a8a; border-left:4px solid #60a5fa; border-radius:0 10px 10px 0; padding:14px 18px; margin:8px 0; }

  .risk-title { font-size:13px; font-weight:700; margin-bottom:4px; }
  .risk-body  { font-size:13px; line-height:1.65; color:#94a3b8; }
  .risk-rec   { font-size:12px; margin-top:8px; padding:8px 12px; background:rgba(255,255,255,0.04); border-radius:6px; color:#cbd5e1; }

  .clause-card {
    background:#0b0d18; border:1px solid #1e2040;
    border-radius:10px; padding:16px 18px; margin:8px 0;
  }
  .clause-type { font-size:12px; font-weight:700; letter-spacing:2px; text-transform:uppercase; margin-bottom:6px; }
  .clause-original { font-size:12px; color:#475569; font-style:italic; margin-bottom:8px; line-height:1.5; }
  .clause-plain { font-size:13px; color:#e2e8f0; line-height:1.65; }
  .clause-tag {
    display:inline-block; padding:2px 8px; border-radius:4px;
    font-size:10px; font-weight:700; margin-left:6px;
  }

  .obligation-row {
    background:#080a14; border:1px solid #1e2040;
    border-radius:8px; padding:12px 16px; margin:6px 0;
    display:grid; grid-template-columns:1fr 2fr 1fr 1fr; gap:12px; align-items:start;
  }

  .stat-card {
    background:#0b0d18; border:1px solid #1e2040;
    border-radius:10px; padding:14px; text-align:center;
  }
  .stat-val   { font-size:22px; font-weight:700; }
  .stat-label { font-size:10px; color:#475569; text-transform:uppercase; letter-spacing:1.5px; margin-top:3px; }

  .recommendation-item {
    background:#050a05; border:1px solid #14532d;
    border-radius:8px; padding:10px 14px; margin:5px 0;
    font-size:13px; color:#86efac; line-height:1.6;
  }
  .red-line-item {
    background:#150205; border:1px solid #7f1d1d;
    border-radius:8px; padding:10px 14px; margin:5px 0;
    font-size:13px; color:#fca5a5; line-height:1.6;
  }

  .disclaimer-box {
    background:#0f0c00; border:1px solid #78350f; border-radius:8px;
    padding:12px 16px; font-size:12px; color:#fcd34d; margin-top:16px;
  }

  div.stButton > button {
    background:linear-gradient(135deg,#1e3a5f,#3b82f6);
    color:white; font-weight:700; border:none; border-radius:10px;
    padding:13px 28px; font-size:15px; width:100%;
  }
  div.stButton > button:hover { opacity:0.85; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚖️ Legal Analyzer")
    st.markdown("---")
    st.markdown("### 🔑 Gemini API Key")
    api_key = st.text_input("Free Gemini API Key", type="password", placeholder="AIza...")
    if not api_key:
        st.info("🆓 Free at [aistudio.google.com](https://aistudio.google.com)")

    st.markdown("---")
    st.markdown("### ⚙️ Settings")
    doc_type_override = st.selectbox(
        "Document type (or auto-detect)",
        ["auto"] + list(DOCUMENT_TYPES.keys()),
        format_func=lambda x: "🔍 Auto-detect" if x == "auto" else DOCUMENT_TYPES[x],
    )

    st.markdown("---")
    st.markdown("### 📄 Load Sample")
    if st.button("📄 Load Sample NDA"):
        st.session_state["doc_text"] = SAMPLE_NDA
    if st.button("💼 Load Sample Employment"):
        st.session_state["doc_text"] = SAMPLE_EMPLOYMENT

    st.markdown("---")
    st.markdown("### ⚠️ Disclaimer")
    st.error("Not legal advice. Always consult a qualified attorney.")

# ── Main ───────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚖️ AI Legal Document Analyzer</h1>
  <p>Upload any contract or paste text → Get risk flags, plain English translations, obligations, and negotiation recommendations</p>
</div>
""", unsafe_allow_html=True)

# ── Document input ─────────────────────────────────────────────────────────────
tab_input, tab_upload = st.tabs(["📝 Paste Text", "📂 Upload File"])

with tab_input:
    doc_text = st.text_area(
        "Paste contract text here",
        value=st.session_state.get("doc_text", ""),
        height=280,
        placeholder="Paste your NDA, employment contract, lease, terms of service, or any legal document here...",
        label_visibility="collapsed",
    )

with tab_upload:
    uploaded = st.file_uploader("Upload .txt or .pdf file", type=["txt", "pdf"])
    if uploaded:
        if uploaded.type == "application/pdf":
            try:
                import fitz
                doc = fitz.open(stream=uploaded.read(), filetype="pdf")
                doc_text = "\n".join(page.get_text() for page in doc)
                st.success(f"✅ Extracted {len(doc_text.split())} words from PDF")
            except ImportError:
                st.warning("Install PyMuPDF for PDF support: `pip install pymupdf`")
                doc_text = ""
        else:
            doc_text = uploaded.read().decode("utf-8", errors="ignore")
            st.success(f"✅ Loaded {len(doc_text.split())} words")

analyse_clicked = st.button("⚖️ Analyse Document")

# ── Analysis ───────────────────────────────────────────────────────────────────
if analyse_clicked:
    text = doc_text.strip() if doc_text else st.session_state.get("doc_text", "").strip()
    if len(text) < 100:
        st.warning("⚠️ Please paste a legal document (at least 100 characters).")
        st.stop()
    if not api_key:
        st.error("⚠️ Please add your free Gemini API key in the sidebar.")
        st.stop()

    progress_bar = st.progress(0, text="Starting analysis...")

    def on_progress(step, total, msg):
        progress_bar.progress(step / total, text=msg)

    try:
        result: LegalAnalysis = analyze_document(
            text=text,
            api_key=api_key,
            doc_type_override=doc_type_override,
            on_progress=on_progress,
        )
        progress_bar.empty()
        st.session_state["result"] = result
        st.success("✅ Analysis complete!")
    except Exception as e:
        progress_bar.empty()
        st.error(f"Analysis failed: {str(e)}")
        st.stop()

# ── Display results ────────────────────────────────────────────────────────────
result: LegalAnalysis = st.session_state.get("result")

if result:
    risk_cfg = RISK_LEVELS.get(result.overall_risk, RISK_LEVELS["medium"])

    # ── Top stats ──────────────────────────────────────────────────────────────
    c1,c2,c3,c4,c5 = st.columns(5)
    risk_color = risk_cfg["color"]
    kpis = [
        (f"{risk_cfg['emoji']} {result.overall_risk.upper()}", risk_color, "Overall Risk"),
        (f"{result.risk_score}/100",                           risk_color, "Risk Score"),
        (len(result.risk_flags),                               "#f97316",  "Risk Flags"),
        (len(result.red_lines),                                "#dc2626",  "Must-Change"),
        (result.word_count,                                    "#60a5fa",  "Word Count"),
    ]
    for col, (val, color, label) in zip([c1,c2,c3,c4,c5], kpis):
        with col:
            st.markdown(f'<div class="stat-card"><div class="stat-val" style="color:{color};">{val}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Document metadata ──────────────────────────────────────────────────────
    m1,m2,m3,m4 = st.columns(4)
    meta = [
        (result.doc_type_label,              "Document Type"),
        (", ".join(result.detected_parties), "Detected Parties"),
        (result.governing_law,               "Governing Law"),
        (result.effective_date,              "Effective Date"),
    ]
    for col, (val, label) in zip([m1,m2,m3,m4], meta):
        with col:
            st.markdown(f'<div class="stat-card"><div class="stat-val" style="font-size:14px;color:#e2e8f0;">{val[:30]}</div><div class="stat-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Executive summary ──────────────────────────────────────────────────────
    st.markdown(f"""
<div style="background:#080a14;border:1px solid #1e2040;border-left:4px solid {risk_color};border-radius:0 12px 12px 0;padding:18px 22px;margin-bottom:20px;">
  <div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:{risk_color};margin-bottom:8px;">📋 EXECUTIVE SUMMARY</div>
  <div style="font-size:14px;line-height:1.8;color:#cbd5e1;">{result.executive_summary}</div>
</div>
""", unsafe_allow_html=True)

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab1,tab2,tab3,tab4,tab5 = st.tabs([
        "🚨 Risk Flags", "📋 Key Clauses", "📌 Obligations",
        "💡 Recommendations", "📊 Analysis"
    ])

    with tab1:
        st.markdown("### 🚨 Risk Flags — Ordered by Severity")
        severity_order = ["critical","high","medium","low","info"]
        sorted_flags   = sorted(result.risk_flags,
                                key=lambda f: severity_order.index(f.severity) if f.severity in severity_order else 5)
        for flag in sorted_flags:
            cfg   = RISK_LEVELS.get(flag.severity, RISK_LEVELS["info"])
            color = cfg["color"]
            st.markdown(f"""
<div class="risk-{flag.severity}">
  <div class="risk-title" style="color:{color};">{cfg['emoji']} [{flag.severity.upper()}] {flag.category}</div>
  <div style="font-size:11px;color:#475569;font-style:italic;margin-bottom:6px;">📍 {flag.line_hint}</div>
  <div style="font-size:12px;color:#64748b;margin-bottom:8px;font-family:monospace;">"{flag.clause_text}"</div>
  <div class="risk-body">{flag.explanation}</div>
  <div class="risk-rec">💡 <b>Recommendation:</b> {flag.recommendation}</div>
</div>
""", unsafe_allow_html=True)

        if not result.risk_flags:
            st.success("✅ No significant risk flags detected!")

    with tab2:
        st.markdown("### 📋 Key Clauses — Plain English")
        fav_colors = {
            "party_a":  ("#fca5a5","bg:#1a0a0a"),
            "party_b":  ("#93c5fd","bg:#0a1020"),
            "balanced": ("#86efac","bg:#051a05"),
            "unclear":  ("#fcd34d","bg:#1a1505"),
        }
        for clause in result.key_clauses:
            fc, _ = fav_colors.get(clause.favorable_to, ("#94a3b8",""))
            unusual_badge = ' <span class="clause-tag" style="background:#1a0f00;color:#f97316;border:1px solid #7c2d12;">UNUSUAL</span>' if not clause.is_standard else ''
            st.markdown(f"""
<div class="clause-card">
  <div class="clause-type" style="color:{fc};">{clause.clause_type}{unusual_badge}</div>
  <div class="clause-original">"{clause.original_text}"</div>
  <div class="clause-plain">{clause.plain_english}</div>
  <div style="margin-top:8px;font-size:11px;color:#475569;">
    Favorable to: <span style="color:{fc};font-weight:600;">{clause.favorable_to.replace('_',' ').title()}</span>
    {'&nbsp;·&nbsp;<span style="color:#f97316;">⚠️ Non-standard</span>' if not clause.is_standard else ''}
  </div>
</div>
""", unsafe_allow_html=True)

    with tab3:
        st.markdown("### 📌 Obligations & Deadlines")
        if result.obligations:
            for ob in result.obligations:
                has_deadline = ob.deadline not in ("No deadline specified","","Ongoing","Not specified")
                dl_color = "#ef4444" if has_deadline else "#475569"
                st.markdown(f"""
<div class="obligation-row">
  <div>
    <div style="font-size:10px;color:#475569;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;">PARTY</div>
    <div style="font-size:13px;color:#60a5fa;font-weight:600;">{ob.party}</div>
  </div>
  <div>
    <div style="font-size:10px;color:#475569;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;">OBLIGATION</div>
    <div style="font-size:13px;color:#e2e8f0;">{ob.action}</div>
  </div>
  <div>
    <div style="font-size:10px;color:#475569;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;">DEADLINE</div>
    <div style="font-size:13px;color:{dl_color};font-weight:{'600' if has_deadline else '400'};">{'⏰ ' if has_deadline else ''}{ob.deadline}</div>
  </div>
  <div>
    <div style="font-size:10px;color:#475569;letter-spacing:1px;text-transform:uppercase;margin-bottom:3px;">IF VIOLATED</div>
    <div style="font-size:12px;color:#94a3b8;">{ob.consequence}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            st.info("No specific obligations extracted.")

    with tab4:
        st.markdown("### 💡 Recommendations")

        if result.red_lines:
            st.markdown("#### 🚫 Red Lines — Must Change Before Signing")
            for item in result.red_lines:
                st.markdown(f'<div class="red-line-item">🚫 {item}</div>', unsafe_allow_html=True)

        if result.negotiation_points:
            st.markdown("#### 🤝 Negotiation Points")
            for item in result.negotiation_points:
                st.markdown(f'<div class="recommendation-item">🤝 {item}</div>', unsafe_allow_html=True)

        if result.quick_wins:
            st.markdown("#### ⚡ Quick Wins — Easy Improvements")
            for item in result.quick_wins:
                st.markdown(f'<div class="recommendation-item">⚡ {item}</div>', unsafe_allow_html=True)

        if result.missing_clauses:
            st.markdown("#### ❌ Missing Standard Clauses")
            for item in result.missing_clauses:
                st.markdown(f'<div style="background:#0a0512;border:1px solid #4c1d95;border-radius:8px;padding:10px 14px;margin:5px 0;font-size:13px;color:#c4b5fd;">❌ {item}</div>', unsafe_allow_html=True)

        if result.unusual_clauses:
            st.markdown("#### ⚠️ Unusual Clauses")
            for item in result.unusual_clauses:
                st.markdown(f'<div class="risk-medium"><div class="risk-body">⚠️ {item}</div></div>', unsafe_allow_html=True)

    with tab5:
        st.markdown("### 📊 Risk Analysis")
        sev_counts = {}
        for f in result.risk_flags:
            sev_counts[f.severity] = sev_counts.get(f.severity,0) + 1

        if sev_counts:
            fig = go.Figure(go.Bar(
                x=list(sev_counts.keys()),
                y=list(sev_counts.values()),
                marker_color=[RISK_LEVELS.get(k,{}).get("color","#94a3b8") for k in sev_counts.keys()],
                text=list(sev_counts.values()),
                textposition="outside",
            ))
            fig.update_layout(
                paper_bgcolor="#07080d", plot_bgcolor="#07080d",
                font_color="#94a3b8", height=280,
                yaxis=dict(title="Count", gridcolor="#1e2040"),
                xaxis=dict(gridcolor="#1e2040"),
                margin=dict(t=10,b=10,l=10,r=10),
                title="Risk Flags by Severity",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Category breakdown
        cat_counts = {}
        for f in result.risk_flags:
            cat_counts[f.category] = cat_counts.get(f.category,0) + 1
        if cat_counts:
            cat_df = pd.DataFrame(list(cat_counts.items()), columns=["Category","Count"])
            fig2 = go.Figure(go.Bar(
                y=cat_df.sort_values("Count")["Category"],
                x=cat_df.sort_values("Count")["Count"],
                orientation="h",
                marker_color="#f97316",
                opacity=0.8,
            ))
            fig2.update_layout(
                paper_bgcolor="#07080d", plot_bgcolor="#07080d",
                font_color="#94a3b8",
                height=max(200, 35*len(cat_counts)+60),
                xaxis=dict(title="Flags", gridcolor="#1e2040"),
                margin=dict(t=10,b=10,l=10,r=10),
                title="Risk Categories",
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Download
        st.download_button(
            "⬇️ Download Full Analysis (.json)",
            data=json.dumps(asdict(result), indent=2, default=str),
            file_name="legal_analysis.json",
            mime="application/json",
        )

    # Disclaimer
    st.markdown(f'<div class="disclaimer-box">⚠️ <b>DISCLAIMER:</b> {result.disclaimer}</div>', unsafe_allow_html=True)

else:
    st.markdown("""
<div style="text-align:center;padding:50px 20px;">
  <div style="font-size:72px;margin-bottom:16px;">⚖️</div>
  <h3 style="color:#475569;">Paste a legal document above or load a sample</h3>
  <p style="color:#334155;font-size:14px;max-width:540px;margin:0 auto 24px;">
    Works with NDAs, employment contracts, leases, service agreements, terms of service,
    partnership agreements, and any other legal document. Paste text or upload a .txt / .pdf file.
  </p>
</div>
""", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    for col, (icon, title, desc) in zip([c1,c2,c3],[
        ("🚨","Risk Detection","Identifies dangerous clauses, unfair terms, and hidden obligations"),
        ("📋","Plain English","Translates complex legalese into clear, simple language"),
        ("💡","Negotiation Guide","Specific red lines, quick wins, and negotiation recommendations"),
    ]):
        with col:
            st.markdown(f'<div style="background:#0b0d18;border:1px solid #1e2040;border-radius:10px;padding:16px;text-align:center;"><div style="font-size:28px;margin-bottom:8px;">{icon}</div><div style="font-weight:600;color:#e2e8f0;margin-bottom:6px;">{title}</div><div style="font-size:12px;color:#475569;">{desc}</div></div>', unsafe_allow_html=True)
