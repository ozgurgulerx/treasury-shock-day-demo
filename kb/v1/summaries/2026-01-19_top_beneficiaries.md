---
doc_type: summary
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-19"
topics:
  - daily_summary
  - beneficiaries
  - concentration
  - risk
snapshot_timestamp: "2026-01-19T12:00:00Z"
---

# Top Beneficiaries Summary - 2026-01-19

## Summary

This document summarizes the top payment beneficiaries by volume for the current business day, highlighting concentration risk.

## Top 10 Beneficiaries by Total Value

| Rank | Beneficiary Name | Total Amount | Currency | Txn Count | % of Daily Total |
|------|------------------|--------------|----------|-----------|------------------|
| 1 | M348934600 | 15,234,500 | TRY | 342 | 18.7% |
| 2 | M1823072687 | 8,456,200 | TRY | 187 | 10.4% |
| 3 | M547558035 | 4,890,100 | TRY | 89 | 6.0% |
| 4 | ACME Trading LLC | 250,000 | USD | 1 | 0.3% |
| 5 | M855959430 | 1,234,500 | TRY | 56 | 1.5% |
| 6 | M480139044 | 987,600 | TRY | 34 | 1.2% |
| 7 | M85975013 | 756,300 | TRY | 28 | 0.9% |
| 8 | M211654091 | 654,200 | TRY | 23 | 0.8% |
| 9 | M1231006815 | 543,100 | TRY | 19 | 0.7% |
| 10 | M1979787155 | 432,000 | TRY | 15 | 0.5% |

## Concentration Analysis

### By Beneficiary

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Top 1 Beneficiary % | 18.7% | 25% | NORMAL |
| Top 5 Beneficiaries % | 35.9% | 50% | NORMAL |
| Top 10 Beneficiaries % | 41.0% | 60% | NORMAL |
| Single Largest Payment | 250,000 USD | 500,000 | NORMAL |

### By Payment Type

| Payment Type | Total Volume | % of Total | Avg Amount |
|--------------|--------------|------------|------------|
| es_transportation | 45,600,000 TRY | 56.0% | 1,245 |
| es_fashion | 12,340,000 TRY | 15.2% | 2,890 |
| es_food | 8,760,000 TRY | 10.8% | 1,567 |
| URGENT_SUPPLIER | 250,000 USD | 0.3% | 250,000 |
| es_health | 7,890,000 TRY | 9.7% | 3,456 |
| es_hyper | 6,540,000 TRY | 8.0% | 987 |

## Notable Beneficiaries

### ACME Trading LLC (TXN-EMRG-001)

| Attribute | Value |
|-----------|-------|
| Payment Amount | 250,000 USD |
| Payment Type | URGENT_SUPPLIER |
| Channel | SWIFT |
| Current Status | QUEUED |
| Entity | BankSubsidiary_TR |
| Account | ACC-BAN-001 |
| First Payment to Beneficiary | Yes (new beneficiary) |
| Sanctions Screening | Required |

**Flags:**
- New beneficiary (no prior transaction history)
- Large single payment relative to daily volume
- Marked as URGENT_SUPPLIER
- Would cause liquidity buffer breach

### High-Frequency Beneficiaries

| Beneficiary | Today Txn Count | 30-Day Avg | Variance |
|-------------|-----------------|------------|----------|
| M348934600 | 342 | 298 | +14.8% |
| M1823072687 | 187 | 201 | -7.0% |
| M547558035 | 89 | 85 | +4.7% |

## Anomaly Alerts

| Alert Type | Beneficiary | Details |
|------------|-------------|---------|
| NEW_BENEFICIARY | ACME Trading LLC | First payment, large amount |
| VOLUME_SPIKE | M348934600 | 14.8% above 30-day average |
| ANOMALY_DETECTED | M547558035 | TXN-000005 flagged for review |

## Recommendations

1. **ACME Trading LLC**: Complete sanctions screening before release
2. **M348934600**: Volume elevated but within tolerance
3. **M547558035**: Review TXN-000005 anomaly flag

---

*Generated: 2026-01-19T12:00:00Z*
*Next Update: 2026-01-19T14:00:00Z*
*Source: treasury.ledger_today*
