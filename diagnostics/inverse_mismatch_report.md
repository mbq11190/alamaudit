# Inverse Relations Fast Validator Report

**Date:** 2025-12-23
**Branch:** fix/inverse-recovery

## Summary
The fast inverse relations validator found multiple One2many fields whose declared comodels do not appear to have a matching `_name` declaration in the repo (or the comodel file could not be confidently identified by the fast scan). This may include false positives due to file-wrapping or formatting differences; it requires manual review to confirm which are true problems.

## Raw findings (excerpt)
(See full list below; each line shows: source-file -> comodel (expected) inverse)

```
- qaco_quality_review/models/quality_review.py -> qaco.quality.eqr.scope (quality_review_id) : NO model found
- qaco_quality_review/models/quality_review.py -> qaco.quality.checklist.line (quality_review_id) : NO model found
- qaco_planning_phase/models/planning_p10_related_parties.py -> qaco.planning.p10.related.party.line (p10_related_parties_id) : NO model found
- qaco_planning_phase/models/planning_p12_strategy.py -> qaco.planning.p12.risk.response (p12_id) : NO model found
- ... (many more)
```

> Note: Many entries may be false positives — e.g. the comodel is present but formatted in a way the fast scanner missed. Manual verification is required per entry.

## Next recommended steps
1. **Collect production traceback** (critical): the KeyError stack trace pinpoints the exact file and field that triggers registry failure — please paste the full traceback or grant temporary access to logs. This is the fastest way to produce a targeted fix.

2. **Manual triage**: for the top N entries (I can prioritize by module or by occurrence), inspect the supposed comodel files and confirm if `_name` exists or if the field name differs. Where mismatch is real, propose the change:
   - Add missing `fields.Many2one(...)` to comodel OR
   - Correct One2many inverse to existing field name

3. **Patch & tests**: prepare minimal PR(s) with the fix, unit tests (or documented scenario), and upgrade plan.

4. **CI safety**: the repo already includes validator scripts and CI job; ensure the validator is strict (not produce false positives) or make it run in diagnostic mode in CI to avoid blocking PRs with false positives.

## Full raw output
```
(Full output from scripts/validate_inverse_relations_fast.py run inserted here)
```

---

If you want, I can begin manual triage on the top 10 entries and prepare the first PR for the highest-likelihood fixes; confirm and I’ll proceed.