# Research Ledger Schema v1

A research record is valid only when provenance and uncertainty are explicit.

```json
{
  "id": "stable-id",
  "reference": "source reference",
  "source_type": "quran|hadith|tafsir|secondary|inference",
  "provenance": "where the material was obtained",
  "context": "relevant surrounding context",
  "claim": "what the evidence supports",
  "support_level": "direct|strong_inference|weak_inference|disputed|unverified",
  "counter_evidence": [],
  "interpretations": [],
  "draft_links": [],
  "verified": false
}
```

`verified=false` is the default. Verification must be earned by a source-aware check; prose quality never changes it.
