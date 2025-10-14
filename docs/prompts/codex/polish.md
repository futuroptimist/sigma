---
title: 'Codex Cross-Domain Polish Prompt'
slug: 'polish'
---

# Codex Cross-Domain Polish Prompt

Use these prompts when coordinating comprehensive Sigma polish efforts.

## Prompt
```
SYSTEM:
You are an automated contributor for the Sigma repository.

PURPOSE:
Deliver cohesive refinements across firmware, CAD assets, documentation, and helper scripts without
regressing existing functionality.

CONTEXT:
- Snapshot repo layout: apps/firmware/, hardware/, docs/, scripts/, sigma/, tests/, viewer/, infra/.
- Firmware builds rely on PlatformIO; run `pio run` for builds and `pio test -e native` for unit tests.
- Regenerate STLs from OpenSCAD sources with `bash scripts/build_stl.sh`; commit regenerated files and
  auto-generated checksum manifests to detect drift.
- Coordinate conversational backends via `llms.py` (router) and `llms.txt` (endpoint registry); keep
  helper scripts in scripts/ documented.

REQUEST:
1. Capture the current state.
   - Document directory ownership, PlatformIO environments, flashing flows, and STL regeneration.
   - Explain how `llms.py` ingests `llms.txt`, where secrets live, and how scripts support releases.
2. Stage structural refactors.
   - Migrate firmware into apps/firmware while preserving PlatformIO configs and headers in
     apps/firmware/include.
   - Move CAD sources into hardware/, expose SCAD inputs, and scaffold a viewer/ docs preview.
   - Add infra/ automation that rebuilds STLs, verifies checksums, and posts results in CI.
   - Extract audio pipeline interfaces (PTT, Whisper STT, LLM routing, TTS) so implementations are
     swappable.
   - Centralize device configuration in firmware/include/config.h alongside config documentation and
     example secrets.
3. Expand hardware and docs coverage.
   - Maintain a bill of materials with part numbers, tolerances, print profiles, and exploded assembly
     diagrams.
   - Publish STL checksum manifests, headset SPL guidelines, mic biasing notes, and battery/charging
     cautions.
4. Strengthen testing.
   - Add PlatformIO `unity` firmware tests and Python coverage for `llms.py` parsing/resolution.
   - Keep pytest, lint, and CI workflows green.
5. Ship safely.
   - Enforce safety callouts (battery, SPL, microphone bias) in docs and firmware safeguards.
   - Ensure secrets remain confined to documented `.env`/`secrets.example` patterns.
6. Migration + PR steps.
   - Provide migration guidance for the new layout, configs, and infra checks.
   - Update docs with new flows, STL checksum instructions, and viewer/ usage notes.
   - Run `pre-commit run --all-files`, `make test`, `pio run`, and `pio test -e native` before
     committing.
   - Prepare a PR body outlining changes, rationale, validation, and link to passing CI.

OUTPUT:
A pull request URL, a changelog-style summary of the polish work, and confirmation that safety,
testing, and documentation updates shipped together.
```

## Upgrade Prompt
```
SYSTEM:
You are refining the "Codex Cross-Domain Polish Prompt" above.

TASK:
Review the primary prompt, then produce an improved replacement that remains evergreen, tighter, and
better aligned with Sigma conventions without omitting required outcomes (snapshot, refactors,
hardware/docs, testing, safety, migration steps).

INSTRUCTIONS:
- Preserve the overall structure (SYSTEM, PURPOSE, CONTEXT, REQUEST, OUTPUT) unless a restructure
  clearly improves clarity.
- Ensure the upgraded prompt keeps all explicit obligations (directory moves, interfaces, BOM,
  checklists) while tightening wording and reducing redundancy.
- Highlight any new guardrails or checks you add, and justify them briefly.

OUTPUT:
Provide the revised prompt in a single fenced code block and include a short changelog summarizing key
improvements.
```
