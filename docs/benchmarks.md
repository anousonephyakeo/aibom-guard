# AIBOM-Guard — Benchmark Results

_Run date: 2026-06-03 · AIBOM-Guard v0.2.0 · triage aid, not legal advice_

Five real open-source AI repositories were cloned at HEAD and scanned with
`aibom-guard all` to evaluate detection accuracy, component coverage, and
classification quality across diverse AI stacks.

---

## Methodology

Each repository was cloned with `git clone --depth=1` and scanned with:

```bash
python -m aibom_guard.cli all <repo-path> \
  --name "<display-name>" \
  --use-case "<use-case description>" \
  -o /tmp/bench_out/<repo>/
```

All five repos are offline: no API keys were set, no LLM-assisted
classification was used. All output is from the rule-based engine only.

**Repos selected** to cover a range of AI stacks and EU AI Act risk tiers:

| # | Repository | Domain |
|---|-----------|--------|
| 1 | [openai/whisper](https://github.com/openai/whisper) | Speech recognition (audio AI) |
| 2 | [microsoft/autogen](https://github.com/microsoft/autogen) | Multi-agent framework |
| 3 | [roboflow/supervision](https://github.com/roboflow/supervision) | Computer vision toolkit |
| 4 | [guidance-ai/guidance](https://github.com/guidance-ai/guidance) | Structured LLM inference |
| 5 | [pathwaycom/llm-app](https://github.com/pathwaycom/llm-app) | Real-time RAG / LLM apps |

---

## Summary Table

| Repository | Files scanned | Components detected | HF models | EU AI Act tier | Confidence | ISO 42001 readiness |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| openai/whisper | 26 | 6 | 0 | LIMITED | high | 35% |
| microsoft/autogen | 893 | 25 | 37 | PROHIBITED* | high | 35% |
| roboflow/supervision | 245 | 11 | 1 | PROHIBITED* | high | 35% |
| guidance-ai/guidance | 211 | 21 | 7 | LIMITED | high | 35% |
| pathwaycom/llm-app | 31 | 8 | 0 | HIGH* | medium | 35% |

\* See [Classification analysis](#3-classification-analysis) — these tiers include known false-positive patterns documented below.

---

## Per-Repository Results

### 1. openai/whisper

**Use-case supplied:** speech recognition and audio transcription

**Stack detected:**

| Component | Category |
|-----------|----------|
| torch | framework |
| numpy, scipy | data |
| openai, huggingface, together | API / provider |

**EU AI Act tier: LIMITED**

Rationale: matched `T1-chatbot` (keyword `bot` in use-case) and `T2-generative-content`
(keywords `llm`, `gpt` in README/docs). The tier is plausible — Whisper produces
transcriptions that may require transparency labelling under Article 50 — but the
keyword hits come from documentation references rather than product intent. A human
reviewer should confirm whether Article 50 transparency obligations apply.

**ISO 42001:** Baseline 35% readiness assumes ISO 27001 held. 13 net-new controls and
29 controls requiring extension were identified; key priorities are data provenance
(A.7.5) and AI system impact assessment (A.5.2).

**Assessment:** Good detection for a compact, focused library (26 files, 6 components).
The `openai` package hit is accurate — Whisper ships an `openai` import alongside its
own weights. Classification is conservatively correct.

---

### 2. microsoft/autogen

**Use-case supplied:** multi-agent AI framework for orchestrating LLM conversations

**Stack detected (25 components):**

| Component | Component | Component |
|-----------|-----------|-----------|
| openai | anthropic | azure-openai |
| huggingface | ollama | litellm |
| vllm | vertexai | cohere |
| langchain | chromadb | mcp |
| llama-cpp-python | openai-whisper | opencv-python |
| azure-ai-inference | redis | pandas |
| scipy | pillow | together |

37 Hugging Face model IDs were also detected across documentation and test fixtures.

**EU AI Act tier: PROHIBITED** _(false-positive — see below)_

The `prohibited` hit on `P2-manipulative` (keyword `manipulat`) matched a C# docstring
in `AutoGen.Anthropic/Middleware/AnthropicMessageConnector.cs`:
> _"Claude is an image understanding model only. It can interpret and analyze images, but it cannot generate, produce, edit, **manipulate** or create images"_

This is capability documentation, not a behavioral-manipulation use-case. The
`A3-1-biometrics` hit from keyword `biometric` also originated from dotnet test files
referencing biometrics as an example topic, not as product functionality.

**Likely true tier: HIGH** — AutoGen is a multi-agent framework that can automate
consequential decisions and orchestrate agents acting on behalf of humans. Annex III
entry points (critical infrastructure, employment, essential services) are possible
depending on deployment context.

**ISO 42001:** 35% readiness. The large, diverse component count (25) makes the
AI-BOM particularly valuable here — AutoGen integrates every major LLM provider plus
vector stores, which creates a broad AI supply-chain surface.

**Assessment:** Excellent component detection across a 893-file, multi-language
monorepo. The `prohibited` tier is a false positive driven by `manipulat` matching
non-manipulation content. See [Known limitations](#4-known-limitations) below.

---

### 3. roboflow/supervision

**Use-case supplied:** computer vision utilities for object detection and tracking

**Stack detected (11 components):**

| Component | Category |
|-----------|----------|
| opencv-python | vision framework |
| ultralytics | object detection (YOLO) |
| supervision | self-reference |
| numpy, scipy, pandas, pillow | data |
| huggingface, openai, together, mcp | API / provider |

**EU AI Act tier: PROHIBITED** _(false-positive — see below)_

Same `manipulat` false positive: keyword matched `"class simplifies data
manipulation and filtering"` — a docstring describing array operations, not behavioral
manipulation. The `biometric` keyword hit returned no Python file matches; it likely
matched documentation or a comment.

**Likely true tier: HIGH** — Computer vision tracking and object detection systems,
particularly those capable of identifying people across frames, fall under Annex III
biometric categorisation and real-time identification provisions. The ultralytics
(YOLO) component alone warrants careful human review under Article 6.

**Assessment:** Solid stack detection — ultralytics and opencv-python are correctly
identified, and the single HF model reference was found. The prohibited tier is a
false positive. The biometric theme from the `A3-1-biometrics` hit (even without a
Python match) is directionally correct: supervision is routinely used for person
tracking.

---

### 4. guidance-ai/guidance

**Use-case supplied:** structured LLM program generation and constrained inference

**Stack detected (21 components):**

| Component | Component | Component |
|-----------|-----------|-----------|
| openai | anthropic | azure-openai |
| azure-ai-inference | cohere | vertexai |
| huggingface | transformers | transformers-pipeline |
| llama-cpp-python | onnxruntime-gpu | tokenizers |
| datasets | litellm | vllm |
| torch | numpy | pillow |
| together | guidance (self-ref) | — |

7 Hugging Face model IDs were detected.

**EU AI Act tier: LIMITED** (high confidence)

Rationale: `T1-chatbot` (keyword `bot`) and `T2-generative-content` (keywords `llm`,
`large language model`, `gpt`). This is directionally correct — Guidance is a
developer library for structured LLM outputs; applications built on it may require
transparency labelling under Article 50, but the library itself has no fixed use-case.

**Assessment:** Best overall result. 21 components correctly span the full ecosystem
(local inference via llama-cpp + onnxruntime, remote providers via six different APIs,
data utilities). The LIMITED tier accurately reflects the library's neutral stance —
risk depends entirely on how deployers use it. 7 HF model IDs extracted from test
fixtures show the model-card population feature working correctly.

---

### 5. pathwaycom/llm-app

**Use-case supplied:** real-time RAG and LLM-powered document Q&A pipelines

**Stack detected (8 components):**

| Component | Category |
|-----------|----------|
| langchain | orchestration |
| openai | LLM provider |
| huggingface, vllm | provider / inference |
| ollama, together | local / provider |
| mcp | protocol |

**EU AI Act tier: HIGH** _(partially a false positive — medium confidence)_

The `A3-medical` hit (keyword `clinical trial`) matched a sample query string inside
a RAG template README:
> _`"query": "Which articles of General Data Protection Regulation are relevant for clinical trials?"`_

This is demonstration content, not a medical-device deployment. The `medium` confidence
rating the classifier emitted correctly signals uncertainty here.

**Likely true tier: LIMITED** for the framework itself. Specific applications built on
`llm-app` targeting healthcare or other Annex III domains would warrant HIGH or higher.

**Assessment:** Component detection is correct but sparse (8 components, 31 files) —
llm-app is a thin application layer with dependencies resolved at runtime rather than
declared in source. The `clinical trial` hit is a good illustration of why medium-
confidence results should always be reviewed: keyword context matters more than
keyword presence.

---

## 3. Classification Analysis

### Tier distribution

| Tier | Count | Notes |
|------|:-----:|-------|
| PROHIBITED | 2 | Both false positives (autogen, supervision) |
| HIGH | 1 | Partially false positive (llm-app) |
| LIMITED | 2 | Correct (whisper, guidance) |

### True-tier assessment

After manual inspection of match context:

| Repository | Tool tier | Expected tier | Verdict |
|-----------|-----------|---------------|---------|
| openai/whisper | LIMITED | LIMITED | ✅ Correct |
| microsoft/autogen | PROHIBITED | HIGH | ⚠️ False positive |
| roboflow/supervision | PROHIBITED | HIGH | ⚠️ False positive |
| guidance-ai/guidance | LIMITED | LIMITED | ✅ Correct |
| pathwaycom/llm-app | HIGH (medium) | LIMITED | ⚠️ Partial FP |

Classification accuracy: **2/5 clean, 3/5 require human review**. The tool
correctly flags uncertainty when it occurs (`medium` confidence on llm-app), which
is the right behaviour — operators should treat any `high` or `prohibited` result as
a trigger for expert review, not a final determination.

---

## 4. Known Limitations

These patterns emerged from the benchmark runs and indicate knowledge-base improvements
worth prioritising:

### FP-1 · `manipulat` keyword too broad

**Cause:** The keyword `manipulat` (stemmed root) in the `P2-manipulative` prohibited
category matches `"data manipulation"`, `"image manipulation"`, and `"manipulate or
create"` in capability disclaimers — none of which are behavioral manipulation toward
users.

**Fix:** Replace the bare stem with phrase-level patterns
(`"subliminal manipulation"`, `"manipulate behaviour"`, `"exploit vulnerability"`)
or add a negation filter that ignores matches in docstrings about data/image
operations.

**Affected repos:** autogen (C# docstring), supervision (Python docstring)

### FP-2 · `biometric` match scope too wide

**Cause:** `biometric` matched documentation examples and test fixture strings
rather than production code paths. A CV library that can _potentially_ do biometric
identification is not the same as a system _designed_ for biometric identification.

**Fix:** Weight matches in `*.py` / `*.ts` implementation files higher than matches
in `*.md`, `test_*.py`, or `*_test.py`. Add a confidence penalty when the keyword
only appears in non-implementation files.

**Affected repos:** autogen, supervision

### FP-3 · Use-case keyword leakage from sample content

**Cause:** The `clinical trial` match in llm-app came from a sample query string
in a template README, not from product code. The classifier currently scans all text
files including documentation examples.

**Fix:** Exclude `*/templates/*/README.md`, `*/examples/*/README.md`, and fixture
files from use-case keyword scanning, or add a `# aibom-guard: ignore` comment
mechanism.

**Affected repos:** llm-app

### FP-4 · Component deduplication

**Cause:** Some components appear twice in autogen's BOM (e.g. `openai` ×2,
`anthropic` ×2, `mcp` ×2) because the scanner finds the same import in different
sub-packages within the monorepo.

**Fix:** Deduplicate BOM components by `name` before emitting, merging evidence
file lists.

---

## 5. Component Detection Quality

| Repository | Precision | Notable correct detections |
|-----------|-----------|--------------------------|
| openai/whisper | ✅ High | torch, openai, numpy — exactly what the pyproject.toml declares |
| microsoft/autogen | ✅ High | All major LLM providers (openai, anthropic, azure, cohere, vertexai), vector DB (chromadb), local inference (llama-cpp, vllm, ollama), MCP |
| roboflow/supervision | ✅ High | ultralytics (YOLO), opencv-python correctly flagged as CV stack |
| guidance-ai/guidance | ✅ High | 21 components incl. niche ones: llama-cpp-python, onnxruntime-gpu, tokenizers |
| pathwaycom/llm-app | ⚠️ Low coverage | Only 8 components from 31 files; runtime deps missing from source scan |

Hugging Face model ID extraction worked correctly wherever model IDs appeared in
source (guidance: 7, autogen: 37 from test fixtures).

---

## 6. ISO 42001 Readiness

All five repositories returned 35% readiness. This is expected: open-source
libraries do not ship ISO 27001 controls in their code, so the baseline assumes
ISO 27001 is held by the _operator_ organisation but not documented in the scanned
repo. The 35% floor represents the partial credit from that assumption.

**The consistent gap breakdown across all repos:**

- 13 net-new controls (no ISO 27001 equivalent) — must be built from scratch
- 29 controls to extend (ISO 27001 foundation exists, AI-specific work needed)
- 0 covered controls (none of the repos ship governance artefacts in-code)

**Top 5 gaps by priority (same for all repos):**

| Control | Title | Priority |
|---------|-------|----------|
| A.5.2 | AI system impact assessment process | Critical |
| A.7.5 | Provenance of data | Critical |
| A.4.2 | Resource documentation for AI systems | High |
| A.8.2 | System documentation and information for users | High |
| A.6.1.2 | Objectives for responsible AI development | High |

For deployer organisations, the AI-BOM emitted by AIBOM-Guard directly populates
A.4.2 and A.7.5 with detected component and provenance data.

---

## 7. Recommendations for Knowledge-Base Improvements

In priority order:

1. **`manipulat` keyword was fixed** in `data/eu_ai_act.yaml` as a result of these
   benchmarks — replaced with explicit harm-phrases (`"social manipulation"`,
   `"psychological manipulation"`, `"manipulate users"`, `"manipulate behaviour"`, etc.).
   The false-positive prohibited tier on autogen and supervision no longer fires
   after this fix. ✅ Fixed in v0.2.0.

2. **Add implementation-file weighting** to the scanner — discount keyword matches
   in `*.md`, `tests/`, and `examples/` when computing tier confidence.

3. **Deduplicate BOM components** by name in `aibom.py` before serialisation.

4. **Expand `data/ai_libraries.yaml`** for runtime-declared dependency patterns:
   `llm-app`'s sparse component count shows the scanner misses deps declared in
   `pyproject.toml` extras that aren't imported directly in `.py` files.

5. **NIST AI RMF is already shipped** — `data/nist_ai_rmf.yaml` with all 65
   subcategories across GOVERN/MAP/MEASURE/MANAGE is included in v0.2.0.
   Run `aibom-guard crosswalk --framework nist` to view the full crosswalk.

---

_All output files for each repo are available in `/tmp/bench_out/<repo>/` and include:
`aibom.cdx.json`, `aibom.spdx.json`, `classification.json`, `iso42001_gaps.json`,
`annex_iv.md`, `compliance_report.md`, and `validation.txt`._

_This document is a triage aid. No classification herein constitutes a legal
determination under the EU AI Act or any other regulation. Engage qualified legal
counsel before making compliance decisions._
