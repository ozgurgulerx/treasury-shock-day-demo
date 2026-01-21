---
doc_type: runbook
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-15"
topics:
  - emergency_payment
  - liquidity
  - sanctions
  - escalation
  - decision_matrix
---

# Emergency Payment Runbook

## 1. Purpose

This runbook provides step-by-step procedures for processing emergency or urgent payment requests that require expedited handling outside normal batch processing cycles.

## 2. Scope

Applies to all payment requests flagged as:
- `URGENT_SUPPLIER`
- `EMERGENCY`
- `CRITICAL_VENDOR`
- Any payment requiring same-day settlement outside standard cutoffs

## 3. Decision Matrix

The following truth table governs all emergency payment decisions:

| Sanctions Result | Liquidity Breach | Before Cutoff | Action | Approver |
|------------------|------------------|---------------|--------|----------|
| BLOCK | * | * | REJECT + Open Case | Compliance Officer |
| ESCALATE | * | * | HOLD + Compliance Review | Compliance Manager + MLRO |
| CLEAR | true | true | HOLD + Partial Release Option | Treasury Manager |
| CLEAR | true | false | REJECT (Cutoff Missed) | Treasury Manager |
| CLEAR | false | true | PROCEED | Payments Operator |
| CLEAR | false | false | REJECT (Cutoff Missed) | Payments Operator |

## 4. Pre-Flight Checks

Before initiating any emergency payment, verify:

1. **Sanctions Screening**: Call `SanctionsScreeningFlow` with beneficiary name
2. **Liquidity Impact**: Call `compute_liquidity_impact` with payment details
3. **Cutoff Time**: Verify current time against `cutoff_time_utc` for the currency/entity

## 5. Procedure: SANCTIONS CLEAR + NO LIQUIDITY BREACH

IF sanctions_result = `CLEAR` AND liquidity_breach = `false` AND before_cutoff = `true`:

1. Payments Operator releases payment via normal channel
2. Record release timestamp in ledger
3. No additional approval required
4. Status: `RELEASED`

## 6. Procedure: SANCTIONS CLEAR + LIQUIDITY BREACH

IF sanctions_result = `CLEAR` AND liquidity_breach = `true`:

### 6.1 Before Cutoff

1. **HOLD** the payment immediately
2. Notify Treasury Manager via escalation channel
3. Treasury Manager evaluates options:
   - **Option A**: Delay payment to next business day
   - **Option B**: Partial release (if divisible)
   - **Option C**: Request emergency funding from GroupTreasuryCo
   - **Option D**: Override with documented business justification
4. IF override selected:
   - Treasury Manager documents justification
   - Head of Treasury provides secondary approval (SoD requirement)
   - Record override reason in audit bundle
5. Status: `HOLD` until resolved, then `RELEASED` or `REJECTED`

### 6.2 After Cutoff

1. **REJECT** the payment
2. Document rejection reason: "Cutoff missed + Liquidity breach"
3. Notify originator of next-day processing option
4. Status: `REJECTED`

## 7. Procedure: SANCTIONS ESCALATE

IF sanctions_result = `ESCALATE`:

1. **HOLD** the payment immediately
2. Generate case package (see `audit_bundle_requirements.md`)
3. Route to Compliance Manager for initial review
4. Compliance Manager determines:
   - **False Positive**: Document reasoning, proceed to liquidity check
   - **Confirmed Match**: Escalate to MLRO
   - **Uncertain**: Request additional KYC/EDD from originator
5. MLRO final decision required for release
6. Status: `HOLD` pending compliance clearance

## 8. Procedure: SANCTIONS BLOCK

IF sanctions_result = `BLOCK`:

1. **REJECT** the payment immediately
2. Generate sanctions case in compliance system
3. Notify Compliance Officer and MLRO
4. File SAR if required per local regulations
5. Do NOT notify beneficiary or originator of sanctions match
6. Status: `REJECTED`

## 9. Escalation Contacts

| Role | Primary | Backup |
|------|---------|--------|
| Treasury Manager | treasury-manager@bank.local | treasury-backup@bank.local |
| Head of Treasury | head-treasury@bank.local | cfo@bank.local |
| Compliance Manager | compliance-mgr@bank.local | compliance-backup@bank.local |
| MLRO | mlro@bank.local | deputy-mlro@bank.local |

## 10. After-Hours Protocol

For emergency payments received after 18:00 UTC:

1. Contact On-Call Treasury Officer via emergency hotline
2. On-Call Officer has authority for payments up to USD 100,000
3. Payments exceeding USD 100,000 require Head of Treasury mobile approval
4. All after-hours approvals require documented callback verification

## 11. Documentation Requirements

Every emergency payment must have:

1. Original payment instruction
2. Sanctions screening result (full JSON response)
3. Liquidity impact assessment (full JSON response)
4. Approval chain with timestamps
5. Any override justifications
6. Final status and release/rejection timestamp

See `audit_bundle_requirements.md` for complete checklist.

## 12. Review and Updates

This runbook is reviewed:
- Quarterly by Treasury Operations
- After any payment incident
- Upon regulatory guidance changes
- Upon system capability changes

---

*Document Owner: Treasury Operations*
*Last Review: 2026-01-15*
*Next Review: 2026-04-15*
