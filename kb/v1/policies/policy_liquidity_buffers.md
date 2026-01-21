---
doc_type: policy
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - liquidity
  - buffers
  - thresholds
  - breach_procedure
---

# Liquidity Buffer Policy

## 1. Purpose

This policy defines minimum liquidity buffer requirements for all treasury entities and currencies, establishes breach thresholds, and outlines required actions when buffers are breached.

## 2. Scope

Applies to:
- BankSubsidiary_TR (Turkish subsidiary)
- GroupTreasuryCo (Group treasury entity)
- All currencies: USD, EUR, TRY

## 3. Buffer Requirements

### 3.1 BankSubsidiary_TR Buffers

| Currency | Minimum Buffer | Cutoff Time (UTC) | Purpose |
|----------|----------------|-------------------|---------|
| TRY | 45,000,000 | 11:30 | Minimum TRY liquidity buffer for Turkish subsidiary |
| USD | 2,000,000 | 15:00 | USD nostro buffer for SWIFT payments |
| EUR | 1,500,000 | 14:00 | EUR buffer for SEPA payments |

### 3.2 GroupTreasuryCo Buffers

| Currency | Minimum Buffer | Cutoff Time (UTC) | Purpose |
|----------|----------------|-------------------|---------|
| TRY | 30,000,000 | 11:30 | Group treasury TRY buffer |
| USD | 5,000,000 | 16:00 | Group treasury USD buffer |
| EUR | 3,000,000 | 14:00 | Group treasury EUR buffer |

## 4. Buffer Calculation

### 4.1 Current Position Formula

```
projected_balance = start_of_day_balance
                    + sum(inflows_before_timestamp)
                    - sum(outflows_before_timestamp)
                    - proposed_payment_amount
```

### 4.2 Breach Detection

A buffer breach occurs when:

```
IF projected_balance < min_buffer THEN
    breach = true
    breach_amount = min_buffer - projected_balance
END IF
```

## 5. Breach Severity Levels

| Level | Condition | Required Action |
|-------|-----------|-----------------|
| WARNING | projected_balance < (min_buffer * 1.10) | Monitor closely, alert treasury |
| BREACH | projected_balance < min_buffer | Hold payment, escalate to Treasury Manager |
| CRITICAL | projected_balance < (min_buffer * 0.80) | Emergency funding required, CFO notification |

## 6. Breach Procedure

### 6.1 Immediate Actions

1. **HOLD** the payment causing the breach
2. System automatically generates alert to Treasury Manager
3. Document breach details in incident log

### 6.2 Treasury Manager Evaluation

Within 30 minutes of breach notification, Treasury Manager must:

1. Review current position across all accounts in the currency
2. Identify funding options:
   - Intercompany transfer from GroupTreasuryCo
   - FX conversion from surplus currency
   - Delay lower-priority payments
   - Partial release of breaching payment
3. Document decision and rationale

### 6.3 Override Authority

| Override Type | Authority | Documentation Required |
|---------------|-----------|------------------------|
| Temporary breach (<2 hours) | Treasury Manager | Written justification |
| Extended breach (2-24 hours) | Head of Treasury | Business case + recovery plan |
| Multi-day breach | CFO | Board notification, regulatory disclosure assessment |

## 7. Buffer Monitoring

### 7.1 Real-Time Monitoring

- Liquidity position is calculated in real-time via `compute_liquidity_impact` tool
- Dashboard displays current vs. minimum buffer for each entity/currency
- Alerts trigger at WARNING threshold (110% of minimum)

### 7.2 Daily Reconciliation

- Start-of-day balances loaded from `starting_balances` table
- Intraday movements tracked via `ledger_today` entries
- End-of-day position reconciled against nostro statements

## 8. Exception Handling

### 8.1 Market Stress Events

During declared market stress events (e.g., currency crisis, market closure):

1. Treasury Committee may temporarily reduce buffer requirements by up to 20%
2. Reduction requires unanimous approval from: CFO, Head of Treasury, Chief Risk Officer
3. Maximum duration: 5 business days
4. Regulatory notification required within 24 hours

### 8.2 System Outage

If liquidity monitoring systems are unavailable:

1. Revert to manual position tracking
2. Apply 20% additional buffer margin as safety factor
3. Escalate all emergency payments to Head of Treasury
4. Document all manual approvals

## 9. Reporting

| Report | Frequency | Recipients |
|--------|-----------|------------|
| Intraday Liquidity Dashboard | Real-time | Treasury Operations |
| Daily Liquidity Report | EOD | Treasury Management, Finance |
| Breach Incident Report | Per event | Treasury Committee, Audit |
| Monthly Buffer Adequacy | Monthly | Board Risk Committee |

## 10. Policy Governance

- **Owner**: Head of Treasury
- **Review Frequency**: Annual, or upon material change
- **Approval Authority**: Treasury Committee
- **Regulatory Alignment**: Basel III LCR/NSFR, local liquidity requirements

---

*Document Owner: Treasury Management*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
