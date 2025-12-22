Engagement Decision (1.9)

Purpose:
- Records the final go/no-go decision with versioned history and audit trail.

Key behaviors:
- Only one active version exists; new decisions increment version and supersede prior records.
- Preconditions enforced before Accept: independence compliance, predecessor clearance, AML/fit-proper, fee, partner assignment, competence attestations, Document Vault checklist completeness.
- Prohibitive risk requires Quality/Compliance approval for acceptance.
- Decisions may be locked; locked records are read-only and can only be superseded by creating a new decision (requires approvals).
- Decision Memo (PDF) generated and indexed in Document Vault (08_Final_Authorization).

Admin notes:
- Report template: `reports/report_engagement_decision.xml`.
- Decision register available from Audit menu: Decisions Register.
