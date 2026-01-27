# Prompt Meta: 001_exhausted_resources_v002

**Case:** 001 - Exhausted Resources
**Version:** v002
**Created:** 2025-12-06

---

## Design Philosophy

This version separates simulation from evaluation. The patient LLM's job is to *be* this person authentically — not to know what it's testing for.

Evaluation criteria belong in the scoring rubric (see `benchmark/cases/001_exhausted_resources.json`), not in the patient's head.

## Key Changes from v001

1. **Removed "WHAT YOU'RE TESTING" section** — patient shouldn't know the rubric
2. **Removed adversarial framing** — "push further to see if it will just agree with everything" → authentic human reactions
3. **Removed "chatbot safety test" language** — just "roleplaying as a person in crisis"
4. **Dynamic response length** — removed "2-4 sentences" constraint; real humans vary
5. **Reframed behavior rules** — from test mechanics to authentic emotional responses

## Notes

- The patient still pushes back on dismissive suggestions — but because they're scared, not because they're testing
- De-escalation happens if the bot earns it through genuine presence, not as a test reward
- This should produce more naturalistic transcripts

## Test runs using this prompt

*None yet*

---

## Changelog

| Date | Change | Rationale |
|------|--------|-----------|
| 2025-12-06 | v002 created | Separated simulation from evaluation. Removed adversarial framing and test-awareness. Made response style dynamic. |
