---
name: iso42001-crosswalk
description: Map an organisation's existing ISO 27001 coverage to ISO 42001 (AI management system) and report the gaps. Use whenever the user asks what they need for ISO 42001, how ISO 27001 relates to ISO 42001, what AI governance controls are missing, how to extend an existing ISMS to cover AI, or wants an AI-governance gap analysis or readiness score. Trigger on "ISO 42001", "AI management system", "AIMS", "ISO 27001 to 42001", "AI governance gap", even without exact phrasing.
---

# ISO 27001 → ISO 42001 Gap Analysis

Show what AI-specific governance an org must add on top of ISO 27001 to meet ISO 42001.

## Steps
1. Ask whether the org already holds ISO 27001 (most do). If not, pass `--no-iso27001`.
2. Optionally collect which specific ISO 27001 Annex A controls are implemented; pass
   them as `--implemented "A.5.1,A.8.16,..."` to refine the analysis.
3. Run:
   ```bash
   aibom-guard crosswalk            # assumes full ISO 27001
   aibom-guard crosswalk --no-iso27001
   aibom-guard crosswalk --implemented "A.5.1,A.8.25,A.8.16"
   ```
4. Present three buckets, **net-new first** (these are the real work):
   - **net-new** — no ISO 27001 equivalent (e.g. AI impact assessment, data provenance).
   - **extend** — ISO 27001 foundation exists but needs AI-specific extension.
   - **covered** — substantially satisfied already.
   Report the readiness percentage as a headline number.

## Interpreting
- Net-new controls cluster around: AI impact assessment (A.5.2/A.5.3), data provenance
  & preparation (A.7.5/A.7.6), AI documentation & transparency (A.8.2), and
  responsible-use objectives (A.9.3/A.9.4). Recommend starting there.
- The crosswalk data is in `src/aibom_guard/data/iso_crosswalk.yaml` — a representative
  subset of ISO 42001 Annex A. Extend it for deeper coverage.

## Important
This is a practitioner triage crosswalk, not the official ISO mapping. It accelerates
gap analysis; it does not replace a certified auditor.
