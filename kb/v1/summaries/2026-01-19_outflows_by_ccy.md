---
doc_type: summary
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-19"
topics:
  - daily_summary
  - outflows
  - currency
  - liquidity
snapshot_timestamp: "2026-01-19T12:00:00Z"
---

# Daily Outflows by Currency - 2026-01-19

## Summary

This document provides a summary of outbound payment volumes by currency for the current business day.

## Outflow Totals by Currency

### BankSubsidiary_TR

| Currency | Total Outflows | Transaction Count | Largest Single | Status |
|----------|---------------|-------------------|----------------|--------|
| TRY | 48,750,000 | 1,847 | 2,500,000 | NORMAL |
| USD | 1,850,000 | 234 | 250,000 | ELEVATED |
| EUR | 890,000 | 156 | 175,000 | NORMAL |

### GroupTreasuryCo

| Currency | Total Outflows | Transaction Count | Largest Single | Status |
|----------|---------------|-------------------|----------------|--------|
| TRY | 32,100,000 | 982 | 1,800,000 | NORMAL |
| USD | 3,200,000 | 145 | 500,000 | NORMAL |
| EUR | 1,450,000 | 89 | 320,000 | NORMAL |

## Buffer Impact Analysis

### BankSubsidiary_TR Position

| Currency | Start Balance | Net Movement | Projected EOD | Buffer | Headroom |
|----------|--------------|--------------|---------------|--------|----------|
| TRY | 48,608,775 | -1,200,000 | 47,408,775 | 45,000,000 | +2,408,775 |
| USD | 2,200,000 | -350,000 | 1,850,000 | 2,000,000 | **-150,000** |
| EUR | 1,800,030 | -120,000 | 1,680,030 | 1,500,000 | +180,030 |

### Key Observations

1. **USD Position at Risk**: BankSubsidiary_TR USD projected to breach buffer by 150,000
2. **Large Queued Payment**: TXN-EMRG-001 for 250,000 USD would increase breach to 400,000
3. **TRY Position Healthy**: Comfortable headroom despite high volume
4. **EUR Position Stable**: Within normal operating range

## Pending High-Value Payments

| TXN ID | Currency | Amount | Beneficiary | Status | Impact |
|--------|----------|--------|-------------|--------|--------|
| TXN-EMRG-001 | USD | 250,000 | ACME Trading LLC | QUEUED | BREACH +250K |
| TXN-000023 | USD | 5.51 | M348934600 | QUEUED | Minimal |
| TXN-000013 | USD | 22.55 | M855959430 | PENDING_APPROVAL | Inflow |

## Recommendations

1. **Treasury Action Required**: Review USD position before 15:00 UTC cutoff
2. **TXN-EMRG-001 Decision**: Requires treasury approval due to liquidity breach
3. **Funding Options**:
   - Intercompany transfer from GroupTreasuryCo (available: 1,800,000 USD)
   - Delay non-urgent USD payments to next day
   - Partial release of TXN-EMRG-001 if divisible

---

*Generated: 2026-01-19T12:00:00Z*
*Next Update: 2026-01-19T14:00:00Z*
*Source: treasury.ledger_today, treasury.starting_balances*
