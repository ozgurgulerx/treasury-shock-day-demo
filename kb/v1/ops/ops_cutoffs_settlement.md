---
doc_type: operations
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - cutoffs
  - settlement
  - payment_windows
  - channels
---

# Payment Cutoffs and Settlement Operations

## 1. Purpose

This document defines payment cutoff times, settlement windows, and operational procedures for ensuring timely payment processing across all channels.

## 2. Scope

Covers all payment channels:
- SWIFT (international wire transfers)
- SEPA (European payments)
- INTERNAL (intercompany transfers)

## 3. Cutoff Times by Entity and Currency

### 3.1 BankSubsidiary_TR

| Currency | Channel | Cutoff (UTC) | Settlement | Notes |
|----------|---------|--------------|------------|-------|
| TRY | INTERNAL | 11:30 | Same-day | Local RTGS cutoff |
| TRY | SWIFT | 11:00 | Same-day | Allow buffer for correspondent |
| USD | SWIFT | 15:00 | Same-day | NY Fed cutoff consideration |
| USD | INTERNAL | 15:30 | Same-day | Internal transfers after SWIFT |
| EUR | SEPA | 14:00 | Same-day | TARGET2 cutoff |
| EUR | SWIFT | 13:30 | Same-day | Allow buffer for SEPA |

### 3.2 GroupTreasuryCo

| Currency | Channel | Cutoff (UTC) | Settlement | Notes |
|----------|---------|--------------|------------|-------|
| TRY | INTERNAL | 11:30 | Same-day | Aligned with subsidiary |
| USD | SWIFT | 16:00 | Same-day | Later cutoff for group |
| USD | INTERNAL | 16:30 | Same-day | Post-SWIFT window |
| EUR | SEPA | 14:00 | Same-day | TARGET2 aligned |
| EUR | SWIFT | 13:30 | Same-day | Standard EUR window |

## 4. Cutoff Enforcement Rules

### 4.1 Standard Payments

```
RULE: CUTOFF_STANDARD_001
IF current_time_utc > cutoff_time_utc THEN
    payment_status = 'REJECTED'
    rejection_reason = 'Cutoff missed for same-day settlement'
    next_available_date = next_business_day()
END RULE
```

### 4.2 Emergency Payments

```
RULE: CUTOFF_EMERGENCY_001
IF payment_type IN ('URGENT_SUPPLIER', 'EMERGENCY') THEN
    IF current_time_utc <= cutoff_time_utc THEN
        process_with_priority = true
    ELSE IF current_time_utc <= (cutoff_time_utc + 30_minutes) THEN
        require_treasury_manager_approval = true
        possible_same_day = true (best efforts)
    ELSE
        reject_for_today = true
        offer_next_day = true
    END IF
END RULE
```

## 5. Settlement Windows

### 5.1 SWIFT Payments

| Phase | Timing (UTC) | Activity |
|-------|--------------|----------|
| Queue Open | 06:00 | Begin processing queued payments |
| Priority Window | 06:00 - 10:00 | High-value/urgent payments |
| Standard Window | 10:00 - 14:00 | Normal batch processing |
| Final Window | 14:00 - cutoff | Remaining payments |
| Reconciliation | cutoff + 2h | Confirm settlements |

### 5.2 SEPA Payments

| Phase | Timing (UTC) | Activity |
|-------|--------------|----------|
| SCT Batch 1 | 07:00 | First SEPA Credit Transfer batch |
| SCT Batch 2 | 11:00 | Second batch |
| SCT Batch 3 | 14:00 | Final batch (cutoff) |
| SDD Processing | 06:00 - 10:00 | Direct Debit submissions |

### 5.3 Internal Transfers

| Phase | Timing (UTC) | Activity |
|-------|--------------|----------|
| Real-time | 00:00 - 23:59 | Process immediately upon approval |
| Batch | Per entity cutoff | End-of-day netting |

## 6. Holiday Calendar

### 6.1 Calendar Sources

- TRY: Turkish banking holidays (TCMB calendar)
- USD: US Federal Reserve holidays
- EUR: TARGET2 calendar (ECB)

### 6.2 Holiday Handling

```
RULE: HOLIDAY_HANDLING_001
IF settlement_date = holiday(currency) THEN
    adjusted_settlement_date = next_business_day(currency)
    IF adjusted_settlement_date > T+2 THEN
        alert_treasury = true
        customer_notification = required
    END IF
END RULE
```

## 7. Pre-Cutoff Procedures

### 7.1 T-60 Minutes (1 hour before cutoff)

1. Review all QUEUED payments for the currency
2. Identify any payments requiring approval
3. Escalate pending approvals to designated approvers
4. Run liquidity projection for remaining payments

### 7.2 T-30 Minutes

1. Final approval push for pending items
2. Prioritize by amount and business criticality
3. Alert Treasury Manager of any at-risk payments
4. Prepare cutoff exception report

### 7.3 T-0 (Cutoff)

1. System automatically rejects new same-day submissions
2. Process any approved payments in final batch
3. Generate cutoff report
4. Begin settlement confirmation monitoring

## 8. Post-Cutoff Procedures

### 8.1 Immediate (Cutoff to Cutoff + 1h)

1. Monitor settlement confirmations
2. Investigate any failed settlements
3. Update payment statuses in ledger
4. Notify originators of any issues

### 8.2 End of Day

1. Reconcile all settled payments against nostro
2. Update starting balances for next day
3. Generate daily settlement report
4. Archive transaction records

## 9. Exception Handling

### 9.1 Missed Cutoff - High Priority Payment

IF payment missed cutoff but business critical:

1. Contact correspondent bank relationship manager
2. Request late processing (may incur fees)
3. Treasury Manager approval required
4. Document exception and fees incurred

### 9.2 Settlement Failure

IF payment fails to settle:

1. Identify failure reason (insufficient funds, sanctions hit, technical)
2. Notify Treasury Manager immediately
3. Determine remediation (resend, investigate, escalate)
4. Update payment status with failure code

### 9.3 System Outage Near Cutoff

1. Activate business continuity procedures
2. Use backup payment channel if available
3. Document all manually processed payments
4. Reconcile immediately upon system restoration

## 10. Reporting

| Report | Timing | Recipients |
|--------|--------|------------|
| Pre-Cutoff Alert | T-60 | Treasury Ops |
| Cutoff Summary | T+15 | Treasury Manager |
| Settlement Confirmation | T+2h | Treasury Ops, Finance |
| Daily Settlement Report | EOD | Treasury Management |
| Exception Report | Per event | Treasury Manager, Audit |

---

*Document Owner: Treasury Operations*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
