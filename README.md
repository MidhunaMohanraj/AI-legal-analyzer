# ⚖️ AI Legal Document Analyzer

<div align="center">

![Banner](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,6,14&height=200&section=header&text=AI%20Legal%20Analyzer&fontSize=50&fontColor=fff&animation=twinkling&fontAlignY=35&desc=Risk%20Detection%20%E2%80%A2%20Plain%20English%20%E2%80%A2%20Obligations%20%E2%80%A2%20Negotiation%20Guide%20%E2%80%A2%20Free%20API&descAlignY=55&descSize=14)

<p>
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-1.35-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Gemini%201.5%20Flash-Free%20API-4285F4?style=for-the-badge&logo=google&logoColor=white"/>
  <img src="https://img.shields.io/badge/10%20Document%20Types-Supported-22C55E?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/PDF%20Support-PyMuPDF-f97316?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge"/>
</p>

<p>
  <b>Paste any legal document → Get risk flags, plain English clause translations, obligation tracking, missing clause detection, and specific negotiation recommendations — powered by Gemini AI.</b>
</p>

> ⚠️ **Educational purposes only. Not legal advice. Always consult a qualified attorney.**

</div>

---

## 🌟 Why This Project?

Most people sign contracts without fully understanding them. Legal language is deliberately complex, and attorney review costs hundreds of dollars per hour. This tool bridges the gap:

```
Before: "The Receiving Party hereby irrevocably assigns to the Disclosing Party
         all right, title, and interest in any inventions, whether or not
         conceived during working hours..."

After AI Analysis:
  🚨 [CRITICAL] IP Assignment
  Clause: "assigns all inventions... whether or not during working hours"
  Risk: You give up ownership of EVERYTHING you create, even personal projects
        built at home with no company resources.
  Recommendation: Add "solely related to Company business" and explicitly
                  carve out personal projects using personal equipment.
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🚨 **Risk Flag Detection** | Critical / High / Medium / Low flags with explanations and recommendations |
| 📋 **Plain English Translation** | Every key clause translated to simple language |
| 📌 **Obligation Tracking** | Who must do what, by when, and consequences if not done |
| ❌ **Missing Clause Detection** | Identifies standard protections that are absent |
| 🤝 **Negotiation Guide** | Specific red lines, quick wins, and negotiation talking points |
| ⚡ **Loaded Language Detection** | Identifies one-sided or dangerous phrasing |
| 📊 **Risk Score** | 0-100 overall risk rating with breakdown by category |
| 🔍 **Auto Document Detection** | Automatically identifies NDA, employment, lease, ToS, etc. |
| 📥 **PDF Support** | Upload PDF files directly for analysis |
| 💾 **JSON Export** | Download complete analysis report |
| 📄 **Sample Documents** | Built-in NDA and Employment contract samples |

---

## 🖥️ Demo

```
⚖️ AI Legal Analyzer — NDA Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 EXECUTIVE SUMMARY
This Non-Disclosure Agreement between TechCorp Inc. and John Smith
contains several critically unfavorable clauses. The 10-year
confidentiality period, unlimited IP assignment, and $500K liquidated
damages are well beyond industry standard. Risk: HIGH (78/100).

🚨 Risk Flags (8 found):

  🚨 [CRITICAL] IP Assignment
  "assigns all inventions... whether or not using Company resources"
  → You give up ownership of personal projects built at home.
  → Recommendation: Add explicit carve-out for personal projects.

  🚨 [CRITICAL] Liquidated Damages
  "liquidated damages of $500,000 per breach"
  → $500K per violation is extremely punitive and non-standard.
  → Recommendation: Negotiate to a reasonable cap tied to actual damages.

  ⚠️ [HIGH] Non-Compete Scope
  "not engage in any business... for 5 years... United States"
  → 5-year national non-compete is likely unenforceable but risky to sign.
  → Recommendation: Limit to 1 year and specific geographic area.

🚫 Red Lines (must change before signing):
  - Remove unlimited IP assignment for personal projects
  - Reduce liquidated damages from $500K
  - Narrow non-compete scope significantly
```

---

## 📦 Installation

```bash
git clone https://github.com/YOUR_USERNAME/ai-legal-analyzer.git
cd ai-legal-analyzer
pip install -r requirements.txt
streamlit run app.py
```

---

## 📄 Supported Document Types

| Type | Examples |
|---|---|
| NDA | Non-disclosure, confidentiality agreements |
| Employment | Job offers, contractor agreements |
| Lease | Apartment, commercial, equipment rental |
| Service Agreement | SaaS contracts, consulting, freelance |
| Terms of Service | ToS, Privacy Policy, EULA |
| Partnership | Business partnership, JV agreements |
| IP Assignment | Work-for-hire, IP transfer |
| Settlement | Legal settlements, release agreements |
| Loan | Credit agreements, promissory notes |
| Purchase | Sales contracts, asset purchases |

---

## 🧠 How It Works

```
Document (text or PDF)
         │
         ▼
┌─────────────────────────────────────────┐
│  Step 1: Document type detection        │
│  Gemini identifies: NDA / Employment /  │
│  Lease / etc. + parties + governing law │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 2: Risk analysis                  │
│  Gemini scans for dangerous clauses:    │
│  liability, IP, non-compete, arbitration│
│  Returns: severity + explanation + rec  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 3: Clause extraction              │
│  Identifies 6-8 key clauses             │
│  Translates each to plain English       │
│  Flags which party each favors          │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 4: Obligation mapping             │
│  Who must do what, by when              │
│  Consequences for non-compliance        │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│  Step 5: Summary + recommendations      │
│  Executive summary, risk score          │
│  Missing clauses, red lines, quick wins │
│  Negotiation talking points             │
└─────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ai-legal-analyzer/
├── app.py                  # 🖥️ Streamlit dashboard — 5 analysis tabs
├── src/
│   └── legal_engine.py     # 🧠 Gemini analysis engine — 5 analysis functions
├── requirements.txt        # 📦 5 dependencies
├── README.md
└── LICENSE
```

---

## 🗺️ Roadmap

- [ ] Side-by-side contract comparison
- [ ] Suggested clause rewrites (not just flags)
- [ ] Jurisdiction-specific analysis
- [ ] Contract scoring vs industry benchmarks
- [ ] Multi-party contract support
- [ ] Browser extension for ToS on any website

---

## 📄 License

MIT — see [LICENSE](LICENSE)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

*Read before you sign.*

![Footer](https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=2,6,14&height=100&section=footer)

</div>
