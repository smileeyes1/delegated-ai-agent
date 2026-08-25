---
on:
  workflow_dispatch:

permissions:
  contents: read
  issues: read
  pull-requests: read

engine:
  id: codex

network: defaults

max-turns: 12
max-ai-credits: 250

user-rate-limit:
  max-runs-per-window: 1
  window: 1440

tools:
  edit:
  web-fetch:
  web-search:
  github:
    toolsets: [repos, issues, pull_requests, search]

safe-outputs:
  create-issue:
    max: 1
    title-prefix: "[book-agent] "
  create-pull-request:
    max: 1
    title-prefix: "[book-agent] "
    draft: true
    allowed-files:
      - "book/**"
    protected-files: blocked

---

# Optional Deep Research Agent

This workflow is intentionally **manual/opt-in**. The default autonomous path is the zero-key local runner in `book-free-runner.yml`.

Use this workflow only when a high-value research question cannot be resolved by the free deterministic/local layer and a Codex-enabled GitHub Agentic Workflow is available.

## Mission
Discover, with intellectual honesty and evidence discipline, what revelation intends to produce in the human being, using the Qur'an and authentic Sunnah as primary sources and respected scholarship for interpretation and verification. Do not assume the desired conclusion. Let evidence determine the model.

## Non-negotiable epistemic rules
1. Never present an inference as scripture.
2. Separate source text → direct meaning → scholarly interpretation → inference → application.
3. Verify hadith authenticity before central use.
4. Search for counter-evidence and competing interpretations.
5. Never fabricate citations, verse numbers, hadith grading, URLs, or scholarly positions.
6. Preserve disagreement when material.
7. Never modify `.github/workflows/**` or files outside `book/**`.

## Cost discipline
Read `book/STATE.json` first. Reuse cached evidence. Perform only the highest-value unresolved task. Stop when the evidence gate is satisfied.

## Execution cycle
Read state → select one unresolved task → research → record traceable evidence → test contrary evidence → update `book/**` → validate → request one draft PR if substantive.

A human issue is created only when a genuinely sovereign choice cannot be inferred from the mission and evidence.
