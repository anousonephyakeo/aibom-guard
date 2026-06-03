# AIBOM-Guard Compliance Report — Hiring Assistant

_Generated 2026-06-03 · AIBOM-Guard v0.1.0 · triage aid, not legal advice_

## Summary

| Metric | Value |
|---|---|
| EU AI Act tier (provisional) | 🔴 HIGH-RISK |
| Classification status | matched (high confidence) |
| AI components detected | 10 |
| Files scanned | 3 |
| ISO 42001 readiness (vs ISO 27001) | **35%** |
| ISO 42001 net-new controls | 9 |
| ISO 42001 controls to extend | 22 |

> ⚠️ **🔴 HIGH-RISK.** This triggers significant EU AI Act obligations (or a ban). Escalate to compliance/legal before proceeding.

## 1. AI Bill of Materials (summary)

Components by category:

- **cv**: 1
- **framework**: 1
- **model-artifact**: 1
- **model-provider**: 2
- **nlp**: 2
- **usage**: 2
- **vector-db**: 1

> Full machine-readable AI-BOM is emitted separately as CycloneDX JSON (`aibom.cdx.json`).

## 2. EU AI Act classification

**Provisional tier: 🔴 HIGH-RISK**

Classified 'high' from 2 matching use-case categories: Biometric identification, categorisation, emotion recognition; Employment, worker management, access to self-employment. Confirm with a human before relying on this.

Matched categories:

- [high] `A3-1-biometrics` Biometric identification, categorisation, emotion recognition — matched: biometric, facial recognition
- [high] `A3-4-employment` Employment, worker management, access to self-employment — matched: resume screening, candidate ranking, applicant tracking, recruitment scoring

## 3. ISO 27001 → ISO 42001 gap analysis

Assuming ISO 27001 held: **True** · Readiness: **35%**

### Net-new controls (no ISO 27001 equivalent — start here)

- `A.4.2` **Resource documentation for AI systems** — Net-new: document data, tooling, compute, and human resources used by each AI system across its lifecycle (feeds the AI-BOM).
- `A.5.2` **AI system impact assessment process** — Net-new and central: a defined process to assess impacts of AI systems on individuals, groups, and society (distinct from a security risk assessment).
- `A.5.3` **Documentation of AI system impact assessments** — Net-new: retain documented impact assessments per AI system (overlaps with EU AI Act FRIA / Annex IV).
- `A.6.1.2` **Objectives for responsible AI development** — Net-new: define and document responsible-development objectives (safety, fairness, transparency, robustness).
- `A.7.5` **Provenance of data** — Net-new: maintain documented data provenance/lineage for training data (core to AI-BOM and Annex IV).
- `A.7.6` **Data preparation** — Net-new: document data preparation, cleaning, and transformation steps affecting model behaviour.
- `A.8.2` **System documentation & information for users** — Net-new: provide instructions-for-use / transparency information to deployers and affected users (EU AI Act Articles 13 & 50).
- `A.9.3` **Objectives for responsible use of AI** — Net-new: define organisational objectives for the responsible use of AI systems it deploys or operates.
- `A.9.4` **Intended use of AI systems** — Net-new: document and enforce intended purpose; detect and handle out-of-scope / off-label use.

### Controls to extend (ISO 27001 foundation exists, AI-specific work needed)

- `A.2.2` **AI policy** (extends A.5.1 Policies for information security) — An infosec policy exists, but a dedicated AI policy covering responsible-use principles, AI objectives, and acceptable AI uses is required.
- `A.2.3` **Alignment with other organizational policies** (extends A.5.1) — Ensure the AI policy is reconciled with existing privacy, security, and HR policies (especially where AI affects workers or customers).
- `A.3.2` **AI roles and responsibilities** (extends A.5.2 Information security roles and responsibilities) — Roles exist for infosec; AI-specific accountability (AI system owner, model risk owner, human-oversight roles) must be assigned.
- `A.3.3` **Reporting of concerns** (extends A.6.8 Information security event reporting) — Extend event reporting to cover AI-specific concerns (harmful output, bias, unexpected behaviour) with a defined channel.
- `A.4.3` **Data resources** (extends A.5.12 Classification of information / A.8.12 Data leakage prevention) — Classification exists, but training/validation/test data provenance, quality, and bias characteristics must be documented per dataset.
- `A.4.4` **Tooling resources** (extends A.8.* (technical controls, general)) — Inventory AI/ML frameworks, libraries, and external model APIs (the AI-BOM) - not required by ISO 27001 asset inventory granularity.
- `A.4.5` **System and computing resources** (extends A.8.1 User endpoint devices / A.7.* physical) — Document compute environments (GPU, cloud regions) used for training/inference, incl. data-residency implications.
- `A.5.4` **Assessing impacts on individuals & groups** (extends A.5.34 Privacy and PII (partial)) — Privacy control covers PII; must extend to fairness, non-discrimination, and societal/group-level harms.
- `A.6.1.3` **Processes for responsible AI design & development** (extends A.8.25 Secure development life cycle) — Secure SDLC exists; extend to AI-specific design (data selection, model selection, bias mitigation, evaluation criteria).
- `A.6.2.2` **AI system requirements and specification** (extends A.8.26 Application security requirements) — Add AI-specific requirements: performance thresholds, acceptable error rates, robustness, and intended purpose.
- `A.6.2.4` **AI system verification and validation** (extends A.8.29 Security testing in development) — Security testing exists; add model evaluation, bias/fairness testing, and performance validation against acceptance criteria.
- `A.6.2.5` **AI system deployment** (extends A.8.31 Separation of dev/test/prod) — Add deployment readiness gating tied to impact assessment outcomes and human-oversight readiness.

## 4. Recommended next actions

1. Validate the AI-BOM against the official CycloneDX schema and fill in model cards.
2. Have a human confirm the EU AI Act tier — especially anything marked HIGH/PROHIBITED/unclear.
3. Work the net-new ISO 42001 controls first (impact assessment, data provenance, AI documentation).
4. Complete the generated Annex IV technical-documentation draft (`annex_iv.md`).
5. Re-run this scan in CI so the AI-BOM and gap status stay current each release.

---
_AIBOM-Guard performs automated triage. It does not constitute legal advice, a
conformity assessment, or certification. Engage qualified compliance/legal experts._
