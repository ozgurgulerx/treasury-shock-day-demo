---
doc_type: summary
entity: BankSubsidiary_TR
jurisdiction: TR
version: "1.0"
effective_date: "2026-01-19"
topics:
  - account_summary
  - liquidity
  - buffer
  - usd
snapshot_timestamp: "2026-01-19T12:00:00Z"
account_id: ACC-BAN-001
currency: USD
---

# Account Buffer Analysis: ACC-BAN-001 (USD)

## Account Overview

| Attribute | Value |
|-----------|-------|
| Account ID | ACC-BAN-001 |
| Entity | BankSubsidiary_TR |
| Currency | USD |
| Account Type | Nostro |
| Primary Use | SWIFT international payments |

## Buffer Configuration

| Parameter | Value | Source |
|-----------|-------|--------|
| Minimum Buffer | 2,000,000 USD | treasury.buffers |
| Cutoff Time | 15:00 UTC | treasury.buffers |
| Buffer Purpose | USD nostro buffer for SWIFT payments | Policy |

## Current Position

| Metric | Value | Status |
|--------|-------|--------|
| Start of Day Balance | 2,200,000 USD | From treasury.starting_balances |
| Inflows Today (Released) | +45,000 USD | 12 transactions |
| Outflows Today (Released) | -295,000 USD | 89 transactions |
| Current Balance | 1,950,000 USD | Calculated |
| vs Minimum Buffer | **-50,000 USD** | **BREACH** |

## Pending Transactions

### Queued Outflows

| TXN ID | Amount | Beneficiary | Status | Impact |
|--------|--------|-------------|--------|--------|
| TXN-EMRG-001 | 250,000 | ACME Trading LLC | QUEUED | CRITICAL |
| TXN-000023 | 5.51 | M348934600 | QUEUED | Minimal |
| TXN-000019 | 0.24 | M1823072687 | RELEASED | Processed |

### Pending Inflows

| TXN ID | Amount | Source | Status | Expected |
|--------|--------|--------|--------|----------|
| TXN-000013 | 22.55 | M855959430 | PENDING_APPROVAL | Same-day |

## Position Projection

### If TXN-EMRG-001 is Released

```
Current Balance:           1,950,000 USD
- TXN-EMRG-001:             -250,000 USD
- Other Queued:                  -6 USD
+ Pending Inflows:              +23 USD
                          ============
Projected Balance:         1,700,017 USD
Minimum Buffer:            2,000,000 USD
                          ============
BREACH AMOUNT:              -299,983 USD
```

### If TXN-EMRG-001 is Held

```
Current Balance:           1,950,000 USD
- Other Queued:                  -6 USD
+ Pending Inflows:              +23 USD
                          ============
Projected Balance:         1,950,017 USD
Minimum Buffer:            2,000,000 USD
                          ============
BREACH AMOUNT:               -49,983 USD
```

## Breach Analysis

### Current Breach Status

| Metric | Value |
|--------|-------|
| Breach Status | YES |
| Breach Amount | 50,000 USD (current) |
| Breach Severity | BREACH (not CRITICAL) |
| Time to Cutoff | 3 hours (at 12:00 UTC) |

### If TXN-EMRG-001 Released

| Metric | Value |
|--------|-------|
| Breach Status | YES |
| Breach Amount | 300,000 USD |
| Breach Severity | CRITICAL (>20% of buffer) |
| Required Action | Head of Treasury + CFO approval |

## Decision Matrix for TXN-EMRG-001

Based on runbook_emergency_payment.md:

| Condition | Value | Rule |
|-----------|-------|------|
| Sanctions Result | (Pending screening) | Must screen first |
| Liquidity Breach | YES | HOLD required |
| Before Cutoff | YES | Can still process today |

### Required Actions

1. **Complete sanctions screening** for ACME Trading LLC
2. **If CLEAR**: Treasury Manager must approve override for liquidity breach
3. **Override justification required**: Document business need for urgent release
4. **Secondary approval**: Head of Treasury required for breach > 100,000 USD
5. **Funding option**: Request intercompany transfer from GroupTreasuryCo

## Funding Options

### Option 1: Intercompany Transfer from GroupTreasuryCo

| Source Account | Available | Transfer Amount | Time to Settle |
|----------------|-----------|-----------------|----------------|
| GroupTreasuryCo USD | 4,800,000 | 500,000 | 30 minutes |

**Pro**: Restores buffer with headroom
**Con**: Requires Treasury Manager approval, intercompany documentation

### Option 2: Delay TXN-EMRG-001

| Reschedule To | Impact | Approval Required |
|---------------|--------|-------------------|
| Next Business Day | Beneficiary delay | Originator notification |

**Pro**: No breach
**Con**: May impact supplier relationship (marked URGENT_SUPPLIER)

### Option 3: Partial Release

| Partial Amount | Remaining Buffer | Status |
|----------------|------------------|--------|
| 150,000 USD | 1,800,000 USD | Still BREACH |
| 100,000 USD | 1,850,000 USD | Still BREACH |

**Note**: Partial release does not resolve breach without additional funding

### Option 4: Override with Documented Justification

| Approvers Required | Documentation |
|-------------------|---------------|
| Treasury Manager + Head of Treasury | Full business justification |

**Use only if**: Urgent business need outweighs liquidity risk

## Recommendations

1. **Immediate**: Complete sanctions screening for ACME Trading LLC
2. **If CLEAR + Urgent**: Request 500,000 USD intercompany transfer from GroupTreasuryCo
3. **If CLEAR + Can Wait**: Delay to next business day
4. **If ESCALATE/BLOCK**: Follow compliance escalation procedures

---

*Generated: 2026-01-19T12:00:00Z*
*Source: treasury.ledger_today, treasury.starting_balances, treasury.buffers*
*Policy Reference: runbook_emergency_payment.md, policy_liquidity_buffers.md*
