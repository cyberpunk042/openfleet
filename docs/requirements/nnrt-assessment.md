---

# NNRT Project Assessment

**Version:** 0.3.0 | **IR Schema:** 0.1.0 | **Status:** Self-described as proof-of-concept; internally rated ~7/10 for trustworthy neutral output

---

## 1. What Is Already Built and Working

**Core pipeline (22 ordered passes, fully wired):**
- `p00_normalize` → `p10_segment` → `p20_tag_spans` → `p22_classify_statements` → `p25_annotate_context` → `p26_decompose` → `p27_epistemic_tag` → `p27b_attribute_statements` → `p27_classify_atomic` → `p28_link_provenance` → `p30_extract_identifiers` → `p32_extract_entities` → `p33_resolve_text_coref` → `p34_extract_events` → `p35_classify_events` → `p36_resolve_quotes` → `p38_extract_items` → `p40_build_ir` → `p42_coreference` → `p43_resolve_actors` → `p44_timeline_v6` → `p46_group_statements` → `p48_classify_evidence` → `p50_policy` → `p55_select` → `p60_augment_ir` → `p70_render` → `p72_safety_scrub` → `p75_cleanup_punctuation` → `p80_package` → `p90_render_structured`

**Policy engine:** Fully operational deterministic rule engine with YAML-driven rulesets (keyword, phrase, regex, quoted, entity-role, entity-type, event-type matching). Supports REMOVE, REPLACE, REFRAME, STRIP, PRESERVE, FLAG, REFUSE, DETECT, CLASSIFY, DISQUALIFY, GROUP, CONTEXT, EXTRACT actions. Token Group Merging with protected ranges prevents accidental modification of quoted speech. Law enforcement and standard profiles exist.

**IR schema:** Rich Pydantic model (`schema_v0_1.py`, ~927 lines) covering Segments, SemanticSpans, Identifiers, Entities (with gender/actor-validation/domain-role), Events (with camera-friendly classification, quality scoring), SpeechActs (with quarantine), Coreference Chains, Mentions, StatementGroups, Timeline (with Allen-style temporal relations, gap detection, multi-day support), EvidenceClassifications, UncertaintyMarkers, PolicyDecisions, TraceEntries, Diagnostics.

**Three registered pipelines:** Default (full), Raw (v1 legacy/debug), Structured-only.

**CLI:** Fully functional with `transform` subcommand, multiple output formats (text, json, ir, structured), pipeline/profile selection, LLM toggle, selection modes (strict/full/timeline/events/recompose), configurable logging.

**Web UI:** Flask server with REST API (`/api/transform`, streaming SSE, `/api/history`, `/api/examples`), HTML/CSS/JS frontend, persisted transformation history (80+ saved runs).

**NLP backends:** Abstracted via interfaces (`NLPBackend` ABC). Implementations: spaCy backend, HuggingFace encoder, JSON-instruct, coreference backend, stub. LLM-based and enhanced event extractors exist.

**Domain configuration system:** YAML-based domain configs (base + law_enforcement) with vocabulary, entity role patterns, event type definitions.

**Invariant/validation infrastructure:** `InvariantRegistry` with HARD/SOFT/INFO severity levels, quarantine system for failed content. Specific invariant modules for quotes, provenance, events. Separate `validate/` package with schema validation, forbidden vocabulary checks, no-new-facts checking, idempotence testing.

**Test suite:** 509 test functions across 44 files. Coverage of individual passes, integration tests, golden tests, hard-case tests, stress tests, an "ultimate challenge" test suite, and V6-specific comparison/question tests.

**Documentation:** Exceptionally thorough — 40+ markdown docs spanning governance, scope/ethics, IR spec, milestones (0-3), architecture analysis (5 versions of gap analysis), design specs, roadmap, and research notes.

**V5 blocking issues:** All 5 resolved (actor resolution, pronoun handling, dependent fragments, mixed quote/narrative, missing actors). Stress-tested with ~7,000-char extreme narratives.

---

## 2. What Is In Progress or Partially Implemented

**V7 "Selection" layer (`p55_select`, `p90_render_structured`):** The selection system and structured renderer exist and are wired into the pipeline, but the `selection/` module (with `models.py`, `epistemic_types.py`, `utils.py`) and multiple render variants (`structured.py`, `structured_v2.py`, `render/structured.py`, `render/constrained.py`, `render/event_generator.py`, `render/template.py`) suggest active iteration. A backup file (`structured_backup_20260118.py`) indicates mid-refactor state.

**Structured output:** The output schema (`docs/schema/nnrt_output_schema_v0.1.yaml`) and `output/structured.py` (Pydantic-based structured output builder) exist, but the presence of both `nnrt/output/structured.py` and `nnrt/render/structured.py` with overlapping responsibilities indicates this boundary is not yet settled.

**V6 timeline features:** Four timeline-related passes exist (`p44_timeline.py`, `p44_timeline_v6.py`, `p44a_temporal_expressions.py`, `p44b_temporal_relations.py`, `p44c_timeline_ordering.py`, `p44d_timeline_gaps.py`), but only `p44_timeline_v6.py` is wired into the default pipeline. The others appear to be decomposed sub-components or alternatives still being evaluated. The `v6/` package (`questions.py`, `comparison.py`) adds investigator question generation and comparison features.

**Coreference resolution:** Two passes exist — `p33_resolve_text_coref` (early, V9 annotation) and `p42_coreference` (post-IR). Both are in the pipeline. The coref backend (`nlp/backends/coref_backend.py`) suggests FastCoref integration is available but may be optional.

**Domain extensibility:** The domain system (`domain/schema.py`, `domain/loader.py`, `domain/integration.py`) has schema and loading infrastructure with two configs (base, law_enforcement). The system is designed for multi-domain support but only law enforcement is fleshed out.

---

## 3. What Is Planned but Not Started

**Milestone 3 capabilities:** The milestone doc describes meta-detection (detecting when transformation is unnecessary/impossible), ambiguity detection, contradiction detection, and sarcasm/irony handling. These are specified but not implemented.

**Future output modes:** `docs/future/MultiOutputMode.md` and `docs/future/FactualReport.md` describe planned output formats beyond the current structured report.

**Production-readiness infrastructure:** The README explicitly states "proof of concept only, not intended for production use." No CI/CD, packaging (no `pyproject.toml` visible in project root — only `.venv`), containerization, or deployment infrastructure exists.

**Additional domain profiles:** The domain system is generic, but only law enforcement is implemented. The docs suggest medical, workplace, and other domains as future targets.

**Phase 5 validation completeness:** `docs/specs/phase5_validation.md` specifies comprehensive validation requirements. The `validation/` directory has infrastructure but only a few invariant modules.

---

## 4. Current Blockers and Quality Issues

**Architectural duplication/drift:**
- Two `validate/` vs `validation/` packages with overlapping concerns
- Multiple render modules (`render/structured.py`, `render/structured_v2.py`, `render/constrained.py`, `render/event_generator.py`, `render/template.py`) plus `output/structured.py` — responsibility boundaries are blurred
- Six timeline-related files, only one wired in
- A backup file (`structured_backup_20260118.py`) committed to the repo

**Pass explosion risk:** 30+ passes in the default pipeline. The pass numbering scheme (p00, p10, p20, p22, p25, p26, p27, p27b, p28, p30, p32, p33, p34, p35, p36, p38, p40, p42, p43, p44, p46, p48, p50, p55, p60, p70, p72, p75, p80, p90) has non-uniform gaps and sub-numbering (p27, p27b, p44a-d) indicating organic growth without periodic consolidation.

**No packaging or distribution:** No `pyproject.toml`, `setup.py`, or `setup.cfg` at project root. The project can't be pip-installed or distributed.

**LLM dependency tension:** The project's core constraint is "deterministic, rule-based, inspectable." The `__init__.py` states "LLMs assist the transformation. LLMs do not define the transformation." However, `llm_event_extractor.py` and `enhanced_event_extractor.py` exist, and the CLI has an `--llm` flag. The boundary between "LLM-assisted" and "LLM-defined" isn't enforced architecturally.

**Global mutable state:** Both `engine.py` and `policy/engine.py` use module-level globals (`_engine`, `_default_profile`) for singleton management. The CLI mutates `os.environ["NNRT_USE_LLM"]` as a feature toggle.

**Governance vs. reality gap:** The governance doc states "code must reference the document that justified its existence" and "if code cannot be explained by a document, it does not belong." Many newer passes (p33, p35, p36, p38, p43, p44a-d, p46, p48, p55, p72, p75, p90) and the entire `selection/`, `domain/`, and `v6/` packages don't have corresponding feature documents.

---

## 5. Where an External Contributor Would Add the Most Value

1. **Packaging and project infrastructure** — Adding `pyproject.toml`, entry points, dependency management, and basic CI. Zero risk to core logic, high enablement value. Unblocks all other external contribution.

2. **Render layer consolidation** — The 6+ render modules and 2 output modules need clear ownership boundaries. An external eye would see the duplication that an incremental developer misses.

3. **Test quality and coverage reporting** — 509 tests exist but there's no coverage measurement, no test categorization (unit vs integration vs golden), and no obvious way to run a quick smoke test vs. the full suite. Adding pytest markers, coverage reporting, and a test matrix would raise confidence significantly.

4. **Second domain profile** — Implementing a non-law-enforcement domain (e.g., workplace, medical) would stress-test the domain abstraction layer and reveal whether the current architecture actually generalizes.

5. **Documentation-to-code traceability** — The governance model demands it but it's not enforced. A contributor could audit which passes have backing docs and which don't, creating a gap report that the project's own governance requires.