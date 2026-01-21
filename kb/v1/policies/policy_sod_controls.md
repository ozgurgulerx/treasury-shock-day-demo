---
doc_type: policy
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - segregation_of_duties
  - sod
  - controls
  - fraud_prevention
---

# Segregation of Duties (SoD) Controls Policy

## 1. Purpose

This policy establishes Segregation of Duties requirements to prevent fraud, errors, and conflicts of interest in treasury payment operations.

## 2. Scope

Applies to all personnel involved in:
- Payment initiation and processing
- Liquidity management
- Sanctions screening
- Reconciliation and reporting

## 3. Core SoD Principles

### 3.1 Four-Eyes Principle

All material transactions require independent review by a second qualified individual who:

1. Did not initiate the transaction
2. Has no reporting relationship to the initiator
3. Has appropriate authority level
4. Performs substantive review (not rubber-stamp)

### 3.2 Separation of Functions

The following functions must be performed by different individuals:

| Function A | Function B | Risk Mitigated |
|------------|------------|----------------|
| Payment Creation | Payment Approval | Unauthorized payments |
| Beneficiary Setup | Payment Release | Fraudulent beneficiaries |
| Sanctions Override | Payment Release | Sanctions evasion |
| Liquidity Override | Override Approval | Unauthorized overrides |
| System Access Admin | Transaction Processing | Privilege abuse |
| Reconciliation | Payment Processing | Concealment of errors |

## 4. Role Definitions

### 4.1 Payments Operations

| Role | Permitted Functions | Prohibited Functions |
|------|--------------------|--------------------|
| Payments Operator | Create payments, submit for approval | Approve own payments, modify beneficiaries |
| Senior Payments Operator | Create, submit, approve others' payments | Approve own payments, system admin |
| Payments Supervisor | Approve payments, override holds | Create payments, system admin |

### 4.2 Treasury

| Role | Permitted Functions | Prohibited Functions |
|------|--------------------|--------------------|
| Treasury Analyst | Create large payments, liquidity monitoring | Approve own payments |
| Treasury Manager | Approve payments, liquidity overrides | Grant own override requests |
| Head of Treasury | Final approval, exception handling | Day-to-day operations |

### 4.3 Compliance

| Role | Permitted Functions | Prohibited Functions |
|------|--------------------|--------------------|
| Compliance Analyst | Screen transactions, flag issues | Release payments, override sanctions |
| Compliance Manager | Approve escalations, clear false positives | Initiate payments |
| MLRO | Final sanctions decisions | Payment operations |

## 5. Specific SoD Rules

### 5.1 Emergency Payment Processing

For emergency payments with sanctions ESCALATE result:

```
RULE: ESCALATE_SOD_001
IF sanctions_result = 'ESCALATE' THEN
    screener_id != approver_id
    AND compliance_reviewer_id != payment_releaser_id
    AND first_approver_id != second_approver_id
END RULE
```

### 5.2 Liquidity Override Processing

For payments causing liquidity buffer breach:

```
RULE: LIQUIDITY_SOD_001
IF liquidity_breach = true THEN
    override_requester_id != override_approver_id
    AND treasury_approver_id != payment_releaser_id
    AND IF override_amount > 500000 THEN
        head_treasury_id != treasury_manager_id
    END IF
END RULE
```

### 5.3 Beneficiary Management

```
RULE: BENEFICIARY_SOD_001
beneficiary_creator_id != beneficiary_approver_id
AND beneficiary_modifier_id != payment_approver_id (for first payment)
AND beneficiary_data_cannot_be_modified_by_payment_processors
```

## 6. SoD Matrix

### 6.1 Incompatible Function Pairs

| Function 1 | Function 2 | Allowed Together? |
|------------|------------|-------------------|
| Create Payment | Approve Payment | NO |
| First Approval | Second Approval | NO |
| Sanctions Screen | Release Payment | NO |
| Request Override | Approve Override | NO |
| Process Payments | Reconcile Payments | NO |
| Admin User Access | Process Transactions | NO |
| Modify Beneficiary | Approve to Beneficiary | NO |
| Set Limits | Approve at Limit | NO |

### 6.2 Compatible Function Pairs

| Function 1 | Function 2 | Allowed Together? |
|------------|------------|-------------------|
| Create Payment | Monitor Queues | YES |
| Approve Payments | Review Reports | YES |
| Sanctions Screen | Escalate Cases | YES |
| Reconciliation | Exception Reporting | YES |

## 7. Technical Controls

### 7.1 System Enforcement

The payment system automatically enforces:

1. **User ID Validation**: Same user cannot approve own transactions
2. **Role-Based Access**: Functions restricted by assigned role
3. **Dual Control**: Sensitive actions require two distinct user IDs
4. **Audit Trail**: All actions logged with user ID and timestamp

### 7.2 Access Reviews

| Review Type | Frequency | Responsibility |
|-------------|-----------|----------------|
| User Access | Quarterly | IT Security + Business Owner |
| Role Assignments | Semi-annually | HR + Department Head |
| SoD Violations | Monthly | Internal Audit |
| Privilege Creep | Annually | IT Security |

## 8. Exception Handling

### 8.1 Temporary SoD Exceptions

In exceptional circumstances (e.g., skeleton staff, emergency):

1. Exception request submitted to Head of Treasury
2. Risk assessment documented
3. Compensating controls identified and implemented
4. Maximum duration: 5 business days
5. Internal Audit notification required

### 8.2 Compensating Controls

When SoD exception granted, implement:

| Missing Control | Compensating Control |
|-----------------|---------------------|
| Dual approval | Same-day supervisor review |
| Separate screener | Post-release compliance review |
| Reconciliation separation | Daily management sign-off |

## 9. Violation Response

### 9.1 Detection

SoD violations detected via:

1. Real-time system blocks (prevented violations)
2. Daily exception reports (technical bypasses)
3. Internal Audit sampling (process violations)
4. Whistleblower reports

### 9.2 Response Protocol

| Violation Type | Initial Response | Investigation |
|----------------|------------------|---------------|
| System blocked | Log and monitor | If repeated, escalate |
| Technical bypass | Immediate escalation | IT Security + Audit |
| Process violation | Supervisor notification | HR + Audit |
| Intentional circumvention | Immediate suspension | HR + Legal + Audit |

## 10. Training Requirements

All personnel must complete:

1. SoD awareness training upon hire
2. Annual SoD refresher
3. Role-specific controls training
4. Acknowledgment of policy understanding

---

*Document Owner: Internal Audit*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
