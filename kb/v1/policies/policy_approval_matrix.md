---
doc_type: policy
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - approvals
  - authority
  - payment_limits
  - delegation
---

# Payment Approval Matrix Policy

## 1. Purpose

This policy defines the approval authority levels for payment processing, including standard payments, emergency payments, and exception handling scenarios.

## 2. Scope

Applies to all outbound payments from:
- BankSubsidiary_TR
- GroupTreasuryCo

## 3. Standard Payment Approvals

### 3.1 By Amount (USD Equivalent)

| Amount Range (USD) | Approver Level | Secondary Approval |
|--------------------|----------------|-------------------|
| 0 - 10,000 | Payments Operator | None |
| 10,001 - 50,000 | Senior Payments Operator | None |
| 50,001 - 250,000 | Treasury Analyst | Payments Supervisor |
| 250,001 - 1,000,000 | Treasury Manager | Treasury Analyst |
| 1,000,001 - 5,000,000 | Head of Treasury | Treasury Manager |
| > 5,000,000 | CFO | Head of Treasury |

### 3.2 By Payment Type

| Payment Type | Base Authority | Additional Requirements |
|--------------|----------------|------------------------|
| INTERNAL | Per amount matrix | None |
| SEPA | Per amount matrix | None |
| SWIFT | Per amount matrix | Beneficiary verification |
| URGENT_SUPPLIER | Treasury Manager minimum | Regardless of amount |
| EMERGENCY | Head of Treasury minimum | CFO for > 1M USD |

## 4. Emergency Payment Approvals

### 4.1 Sanctions-Related

| Sanctions Result | Required Approvers | Timeline |
|------------------|-------------------|----------|
| CLEAR | Per standard matrix | Normal SLA |
| ESCALATE | Compliance Manager + MLRO | Within 4 hours |
| BLOCK | Compliance Officer (rejection only) | Immediate |

### 4.2 Liquidity Breach Scenarios

| Breach Severity | Required Approvers | Override Authority |
|-----------------|-------------------|-------------------|
| No Breach | Per standard matrix | N/A |
| WARNING (110% buffer) | Treasury Manager notification | Treasury Manager |
| BREACH (100% buffer) | Treasury Manager + documented justification | Head of Treasury |
| CRITICAL (80% buffer) | Head of Treasury + CFO | CFO only |

## 5. Combined Scenario Matrix

| Sanctions | Liquidity | Amount > 250K | Required Approvers |
|-----------|-----------|---------------|-------------------|
| CLEAR | No Breach | No | Per standard matrix |
| CLEAR | No Breach | Yes | Treasury Manager + Secondary |
| CLEAR | BREACH | No | Treasury Manager |
| CLEAR | BREACH | Yes | Head of Treasury |
| ESCALATE | Any | Any | Compliance Manager + MLRO + Treasury approver |
| BLOCK | Any | Any | Compliance Officer (rejection) |

## 6. Delegation of Authority

### 6.1 Temporary Delegation

When a designated approver is unavailable:

| Primary Approver | Delegate | Maximum Duration |
|------------------|----------|------------------|
| Payments Operator | Any trained operator | Indefinite |
| Treasury Analyst | Senior Payments Operator | 5 business days |
| Treasury Manager | Head of Treasury | 10 business days |
| Head of Treasury | CFO | 20 business days |
| CFO | CEO | As required |

### 6.2 Delegation Requirements

1. Written delegation must be on file before absence
2. Delegate must have completed required training
3. Delegate cannot approve their own transactions
4. All delegated approvals logged with delegation reference

## 7. Segregation of Duties (SoD)

### 7.1 Prohibited Combinations

No single individual may:

1. **Create AND approve** the same payment
2. **Approve first AND approve second** on dual-approval payments
3. **Request override AND grant override** for same transaction
4. **Screen beneficiary AND release payment** for same transaction

### 7.2 Minimum Separation

| Function | Must Be Separate From |
|----------|----------------------|
| Payment Initiation | Payment Approval |
| Sanctions Screening | Payment Release |
| Liquidity Override | Override Approval |
| Reconciliation | Payment Processing |

## 8. After-Hours Approvals

### 8.1 On-Call Authority

| Role | After-Hours Limit (USD) | Escalation Path |
|------|------------------------|-----------------|
| On-Call Treasury Officer | 100,000 | Head of Treasury mobile |
| Head of Treasury (mobile) | 1,000,000 | CFO mobile |
| CFO (mobile) | Unlimited | Board Chair |

### 8.2 After-Hours Requirements

1. Mobile approval requires callback verification
2. Voice recording of approval conversation
3. Written confirmation within 2 hours via secure email
4. Full documentation by next business day

## 9. System Enforcement

### 9.1 Automated Controls

The payment system enforces:

1. Amount-based routing to appropriate approval queue
2. Prevention of self-approval
3. Dual-approval enforcement for amounts > 50,000 USD
4. Timeout escalation after 2 hours in queue

### 9.2 Manual Override

System overrides require:

1. IT Security approval for system-level bypass
2. Head of Treasury business approval
3. Full audit trail with reason code
4. Review by Internal Audit within 5 business days

## 10. Audit Requirements

All approvals must be:

1. Time-stamped with UTC timestamp
2. Linked to approver identity (non-repudiable)
3. Retained for 7 years minimum
4. Available for regulatory inspection within 24 hours

---

*Document Owner: Treasury Operations*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
