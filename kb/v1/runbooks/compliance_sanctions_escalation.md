---
doc_type: runbook
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - sanctions
  - escalation
  - compliance
  - ofac
  - screening
---

# Sanctions Screening Escalation Runbook

## 1. Purpose

This runbook provides procedures for handling sanctions screening results, including escalation paths for BLOCK and ESCALATE decisions.

## 2. Scope

Applies to all payments screened against:
- OFAC SDN List (primary)
- EU Consolidated Sanctions List
- UN Security Council Sanctions
- Local regulatory lists

## 3. Screening Decision Definitions

### 3.1 Decision Levels

| Decision | Confidence | Match Type | Meaning |
|----------|------------|------------|---------|
| BLOCK | 98%+ | EXACT | Direct match to sanctioned entity |
| BLOCK | 90%+ | FUZZY_HIGH | Very high confidence fuzzy match (score >= 8) |
| ESCALATE | 75%+ | FUZZY_MEDIUM | Medium confidence match (score 4-8) |
| ESCALATE | 60%+ | PARTIAL | Partial name match (score 2-4) |
| CLEAR | 0% | NONE | No matches found |

### 3.2 Response JSON Structure

```json
{
  "decision": "BLOCK|ESCALATE|CLEAR",
  "confidence": 0-100,
  "match_type": "EXACT|FUZZY_HIGH|FUZZY_MEDIUM|PARTIAL|NONE",
  "search_score": 0.0-15.0,
  "best_match": {
    "uid": "string",
    "primary_name": "string",
    "aka_names": ["array"],
    "programs": ["array"],
    "entity_type": "Entity|Individual|Vessel|Aircraft",
    "remarks": "string"
  }
}
```

## 4. Procedure: CLEAR Result

IF decision = `CLEAR`:

1. Payment proceeds to liquidity check
2. No compliance review required
3. Screening result stored for audit trail
4. Status: Continue processing

## 5. Procedure: ESCALATE Result

IF decision = `ESCALATE`:

### 5.1 Immediate Actions

1. **HOLD** payment immediately
2. Generate escalation case package
3. Route to Compliance Analyst queue
4. Notify originator of hold (generic message, no sanctions details)

### 5.2 Compliance Analyst Review (within 2 hours)

1. Review match details and confidence score
2. Compare beneficiary details against match:
   - Full legal name
   - Country of registration/residence
   - Date of birth (individuals)
   - Identification numbers
3. Check additional data sources:
   - KYC records
   - Previous transaction history
   - Adverse media

### 5.3 Analyst Determination

| Finding | Action | Approver |
|---------|--------|----------|
| False Positive - Clear evidence | Clear with documentation | Compliance Analyst |
| False Positive - Requires judgment | Escalate to Compliance Manager | Compliance Manager |
| Potential True Match | Escalate to MLRO | MLRO |
| True Match Confirmed | Convert to BLOCK | MLRO |

### 5.4 False Positive Documentation

Required for false positive clearance:

1. Specific evidence disproving match (different DOB, different country, etc.)
2. Source of verification (KYC docs, public records)
3. Analyst name and timestamp
4. Compliance Manager sign-off (if required)

### 5.5 Escalation to MLRO

If potential true match:

1. MLRO reviews within 4 hours
2. May request additional EDD from originator
3. May consult external sanctions counsel
4. Final decision documented with rationale

## 6. Procedure: BLOCK Result

IF decision = `BLOCK`:

### 6.1 Immediate Actions

1. **REJECT** payment immediately
2. Do NOT release to beneficiary under any circumstances
3. Do NOT notify beneficiary or originator of sanctions match
4. Generate sanctions case in compliance system
5. Notify Compliance Officer and MLRO immediately

### 6.2 Case Package Contents

1. Payment instruction details
2. Screening result (full JSON)
3. Matched SDN entry details
4. Programs matched (IRAN, SDGT, etc.)
5. Entity type and remarks

### 6.3 Regulatory Reporting

| Jurisdiction | Reporting Requirement | Timeline |
|--------------|----------------------|----------|
| US (OFAC) | File blocking report | 10 business days |
| UK | File OFSI report | 20 business days |
| EU | Notify national authority | Per member state |
| Turkey | Notify MASAK | Immediate |

### 6.4 SAR Filing

Evaluate for SAR filing if:

1. Pattern of attempted sanctions evasion
2. Structuring to avoid screening
3. Suspected terrorist financing
4. Money laundering indicators

### 6.5 Originator Communication

Standard response only:

```
"Your payment request could not be processed due to compliance review.
Please contact our compliance team for further information."
```

Do NOT mention:
- Sanctions
- Blocked
- OFAC
- Any match details

## 7. OFAC Programs Reference

### 7.1 High-Risk Programs

| Program | Code | Geographic Focus |
|---------|------|------------------|
| Iran | IRAN, IRAN-EO13902 | Iran |
| North Korea | DPRK, DPRK2 | North Korea |
| Syria | SYRIA | Syria |
| Russia | RUSSIA-EO14024 | Russia |
| Terrorism | SDGT, FTO | Global |

### 7.2 Program-Specific Handling

```
RULE: PROGRAM_PRIORITY_001
IF program IN ('SDGT', 'FTO', 'IRAN', 'DPRK') THEN
    priority = CRITICAL
    mlro_notification = IMMEDIATE
    regulatory_timeline = EXPEDITED
END RULE
```

## 8. Escalation Contacts

| Role | Responsibility | Contact |
|------|----------------|---------|
| Compliance Analyst | Initial ESCALATE review | compliance-analyst@bank.local |
| Compliance Manager | Complex false positives, policy questions | compliance-mgr@bank.local |
| MLRO | Final sanctions decisions, regulatory reporting | mlro@bank.local |
| Sanctions Counsel | Legal interpretation, OFAC queries | legal-sanctions@bank.local |

## 9. Timeline Requirements

| Stage | Maximum Duration |
|-------|------------------|
| Initial HOLD | Immediate upon ESCALATE/BLOCK |
| Analyst Review | 2 hours from escalation |
| Manager Review | 4 hours from analyst escalation |
| MLRO Decision | 24 hours from referral |
| Regulatory Filing | Per jurisdiction requirement |

## 10. Quality Assurance

### 10.1 False Positive Monitoring

- Track false positive rate by match type
- Review threshold calibration quarterly
- Adjust fuzzy match sensitivity if needed

### 10.2 Case Sampling

- Internal Audit samples 10% of ESCALATE cases monthly
- Review for consistent application of procedures
- Identify training needs

## 11. Training Requirements

| Role | Training | Frequency |
|------|----------|-----------|
| All staff | Sanctions awareness | Annual |
| Payments Ops | Screening procedures | Annual |
| Compliance | Advanced sanctions | Semi-annual |
| MLRO | Regulatory updates | Quarterly |

---

*Document Owner: Compliance*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
