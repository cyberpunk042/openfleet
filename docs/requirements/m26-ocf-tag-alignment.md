# M26: ocf-tag Alignment with Existing Ecosystem

## Existing Projects

### NNRT (Narrative-to-Neutral Report Transformer)
- **Repo**: github.com/cyberpunk042/Narrative-to-Neutral-Report-Transformer
- **Status**: Active development, Python, has NLP pipeline, tests, CLI, web interface
- **Architecture**: Full pipeline — segmentation, linguistic decomposition, claim extraction, observation vs interpretation classification, neutral rewriting, uncertainty annotation
- **Milestones**: 4 milestones defined (M0-M3), M3 covers intelligence + edge cases (contradiction detection, ambiguity, meta-detection)
- **Docs**: Extensive — architecture, design, specs, roadmap, governance, schema, IR spec

### FactualReport (Architecture Document)
- **Location**: NNRT repo, docs/future/FactualReport.md
- **Defines the 3-layer architecture**:
  1. **NNRT** (Atomic Layer) — deterministic text-to-neutral transformer
  2. **Factual Engine** (Middleware Layer) — pipeline orchestration, schema enforcement, metadata, confidence annotation
  3. **Factual Platform** (Conceptual Surface) — optional public interface

## What ocf-tag Needs from Each Layer

### From NNRT
- Neutralized input for the Intake layer (Layer 1)
- Claim extraction for structuring (Layer 2)
- Contradiction detection for mapping (Layer 3)
- Neutral report generation for pressure output (Layer 4)

### From Factual Engine
- Confidence scoring
- Cross-report consistency analysis
- Versioned neutrality guarantees
- Audit trail for claim-to-outcome linking

### From Factual Platform
- Public persistence (Layer 5)
- Accountability dashboards (Layer 4)
- Search and discovery

## ocf-tag's Governance Role

ocf-tag does NOT own these products. They exist independently. ocf-tag's role is to:

1. **Align** — ensure its requirements fit the existing architecture
2. **Contribute** — the fleet builds features that NNRT and the Engine need
3. **Validate** — verify that contributions meet the existing project's standards
4. **Integrate** — connect ocf-tag's layers to the products as they mature
5. **Hold accountable** — track whether integration points work, flag regressions

## Revised Phase 5 Approach

Instead of building NNRT/Engine/Platform from scratch:

1. Study and understand the existing NNRT codebase
2. Identify what's already built vs what ocf-tag needs
3. Contribute features to NNRT that serve both projects
4. Build the Factual Engine as an extension/wrapper of NNRT
5. Build the Platform as a new project that consumes the Engine

The fleet works ON the existing NNRT repo, not in parallel to it.