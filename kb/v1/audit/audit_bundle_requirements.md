---
doc_type: audit
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - audit
  - documentation
  - evidence
  - compliance
  - record_keeping
---

# Audit Bundle Requirements

## 1. Purpose

This document defines the required documentation and evidence for all payment decisions, ensuring complete audit trails for regulatory examination and internal review.

## 2. Scope

Applies to all payment decisions, with enhanced requirements for:
- HOLD decisions
- REJECT decisions
- Override approvals
- Sanctions escalations
- Liquidity breach scenarios

## 3. Standard Audit Bundle

### 3.1 Required for ALL Payments

Every processed payment must have:

| Item | Source | Retention |
|------|--------|-----------|
| Payment instruction | Originating system | 7 years |
| Beneficiary details | Payment message | 7 years |
| Sanctions screening result | SanctionsScreeningFlow | 7 years |
| Approval chain | Workflow system | 7 years |
| Final status and timestamp | Ledger | 7 years |

### 3.2 Minimum Data Fields

```json
{
  "payment": {
    "txn_id": "string (required)",
    "timestamp_utc": "ISO8601 (required)",
    "entity": "string (required)",
    "account_id": "string (required)",
    "beneficiary_name": "string (required)",
    "amount": "decimal (required)",
    "currency": "string (required)",
    "payment_type": "string (required)",
    "channel": "SWIFT|SEPA|INTERNAL (required)"
  },
  "screening": {
    "decision": "CLEAR|ESCALATE|BLOCK (required)",
    "confidence": "integer (required)",
    "workflow_run_id": "string (required)",
    "timestamp_utc": "ISO8601 (required)"
  },
  "approval": {
    "approver_id": "string (required)",
    "approval_timestamp": "ISO8601 (required)",
    "approval_level": "string (required)"
  },
  "final_status": {
    "status": "RELEASED|REJECTED|HOLD (required)",
    "status_timestamp": "ISO8601 (required)"
  }
}
```

## 4. Enhanced Bundle: HOLD Decisions

### 4.1 Additional Requirements for HOLD

| Item | Description | Source |
|------|-------------|--------|
| Hold reason code | PRIMARY_REASON | Decision engine |
| Liquidity impact assessment | Full JSON response | LiquidityGate |
| Projected position | Balance after payment | LiquidityGate |
| Buffer threshold | Applicable minimum | Buffers table |
| Breach amount | Shortfall if applicable | Calculated |
| Escalation trail | All notifications sent | Workflow |
| Resolution actions | Steps taken to resolve | Manual entry |

### 4.2 Hold Reason Codes

| Code | Description | Required Evidence |
|------|-------------|-------------------|
| HOLD_SANC_ESC | Sanctions ESCALATE | Screening result + review notes |
| HOLD_LIQ_BREACH | Liquidity breach | Impact assessment + buffer data |
| HOLD_DUAL_APPROVAL | Awaiting second approval | First approval details |
| HOLD_MANUAL_REVIEW | Manual intervention required | Review request details |

### 4.3 Resolution Documentation

For each HOLD that is resolved:

```json
{
  "resolution": {
    "original_hold_reason": "string",
    "resolution_action": "RELEASED|REJECTED|MODIFIED",
    "resolution_timestamp": "ISO8601",
    "resolver_id": "string",
    "resolution_notes": "string",
    "supporting_evidence": ["array of document references"]
  }
}
```

## 5. Enhanced Bundle: REJECT Decisions

### 5.1 Additional Requirements for REJECT

| Item | Description | Retention |
|------|-------------|-----------|
| Rejection reason code | Specific reason | 7 years |
| Rejection timestamp | UTC time | 7 years |
| Originator notification | Proof of notice | 7 years |
| Sanctions case (if BLOCK) | Full case file | Permanent |
| Compliance sign-off (if applicable) | Approval record | 7 years |

### 5.2 Rejection Reason Codes

| Code | Description | Automatic/Manual |
|------|-------------|------------------|
| REJ_SANC_BLOCK | Sanctions BLOCK result | Automatic |
| REJ_CUTOFF_MISSED | Past settlement cutoff | Automatic |
| REJ_LIQ_NO_OVERRIDE | Liquidity breach, no override approved | Manual |
| REJ_COMPLIANCE | Compliance rejection (non-sanctions) | Manual |
| REJ_ORIGINATOR_CANCEL | Originator requested cancellation | Manual |
| REJ_INVALID_DETAILS | Invalid payment details | Automatic |

## 6. Enhanced Bundle: Override Approvals

### 6.1 Override Documentation Requirements

Any override of standard controls requires:

| Item | Description | Mandatory |
|------|-------------|-----------|
| Override type | What control was overridden | Yes |
| Override requester | Who requested | Yes |
| Override approver | Who approved | Yes |
| Business justification | Why override was necessary | Yes |
| Risk acknowledgment | Risks accepted | Yes |
| Compensating controls | Alternative controls applied | If applicable |
| Expiry | If time-limited | If applicable |

### 6.2 Override Types

| Type | Required Approver | Additional Evidence |
|------|-------------------|---------------------|
| Liquidity buffer override | Treasury Manager + Head of Treasury | Funding plan |
| Cutoff extension | Treasury Manager | Correspondent confirmation |
| Dual approval waiver | Head of Treasury | Temporary delegation |
| Sanctions false positive | Compliance Manager + MLRO | Evidence of distinction |
| Amount limit override | Per approval matrix | Business justification |

### 6.3 Override Audit Record

```json
{
  "override": {
    "override_id": "string",
    "override_type": "string",
    "original_control": "string",
    "payment_txn_id": "string",
    "requester_id": "string",
    "requester_timestamp": "ISO8601",
    "approver_id": "string",
    "approver_timestamp": "ISO8601",
    "business_justification": "string (min 50 chars)",
    "risk_acknowledgment": true,
    "secondary_approver_id": "string (if required)",
    "secondary_approval_timestamp": "ISO8601 (if required)"
  }
}
```

## 7. Enhanced Bundle: Sanctions Escalation

### 7.1 ESCALATE Case Package

| Item | Description | Source |
|------|-------------|--------|
| Screening result | Full JSON response | SanctionsScreeningFlow |
| Matched entity details | SDN record | OFAC index |
| Match comparison | Side-by-side analysis | Compliance |
| False positive evidence | Supporting documents | Compliance |
| Review chain | All reviewers and decisions | Workflow |
| Final determination | CLEARED/CONVERTED_TO_BLOCK | Compliance |

### 7.2 BLOCK Case Package

| Item | Description | Retention |
|------|-------------|-----------|
| All ESCALATE items | As above | Permanent |
| Regulatory filing | OFAC/OFSI report | Permanent |
| SAR filing (if applicable) | SAR reference | Permanent |
| Legal consultation | Counsel advice | Permanent |
| Board notification | If required | Permanent |

## 8. Evidence Appendix Format

### 8.1 Standard Appendix Structure

```
AUDIT_BUNDLE_{TXN_ID}/
├── 01_payment_instruction.json
├── 02_sanctions_screening.json
├── 03_liquidity_impact.json (if applicable)
├── 04_approval_chain.json
├── 05_final_status.json
├── 06_override_records/ (if applicable)
│   └── override_{n}.json
├── 07_compliance_review/ (if applicable)
│   ├── case_notes.md
│   └── evidence/
├── 08_communications/
│   └── originator_notification.json
└── 09_audit_metadata.json
```

### 8.2 Audit Metadata

```json
{
  "audit_metadata": {
    "bundle_version": "1.0",
    "created_timestamp": "ISO8601",
    "created_by_system": "string",
    "last_modified": "ISO8601",
    "document_count": "integer",
    "retention_classification": "STANDARD|EXTENDED|PERMANENT",
    "retention_expiry": "ISO8601 or null",
    "regulatory_holds": ["array of hold references"]
  }
}
```

## 9. Quality Checklist

### 9.1 Pre-Archive Checklist

Before archiving any audit bundle:

- [ ] All required documents present
- [ ] All timestamps in UTC ISO8601 format
- [ ] All approver IDs valid and active at time of approval
- [ ] Sanctions screening result matches decision
- [ ] Liquidity assessment matches hold reason (if applicable)
- [ ] Override justification meets minimum length (50 chars)
- [ ] No PII in plain text (encrypted or tokenized)
- [ ] Document hashes calculated for integrity

### 9.2 Completeness Score

| Score | Meaning | Action |
|-------|---------|--------|
| 100% | All required items present | Archive |
| 90-99% | Minor items missing | Review and complete |
| <90% | Significant gaps | Escalate to supervisor |

## 10. Retrieval Requirements

### 10.1 Regulatory Request

- Retrieve within 24 hours of request
- Provide in requested format (PDF, JSON, original)
- Include chain of custody documentation
- Log all access for regulatory requests

### 10.2 Internal Audit Request

- Retrieve within 48 hours of request
- Sampling requests may use bulk export
- Maintain access log

---

*Document Owner: Internal Audit*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
