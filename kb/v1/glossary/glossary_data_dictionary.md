---
doc_type: glossary
entity: ALL
jurisdiction: GLOBAL
version: "1.0"
effective_date: "2026-01-01"
topics:
  - glossary
  - data_dictionary
  - definitions
  - tool_outputs
---

# Glossary and Data Dictionary

## 1. Purpose

This document provides definitions for all terms, data fields, and tool outputs used in the Emergency Payment system.

## 2. Acronyms and Abbreviations

| Acronym | Full Form | Definition |
|---------|-----------|------------|
| AML | Anti-Money Laundering | Regulations and procedures to prevent money laundering |
| CFT | Counter Financing of Terrorism | Measures to prevent terrorist financing |
| EDD | Enhanced Due Diligence | Additional verification for high-risk relationships |
| FX | Foreign Exchange | Currency conversion |
| KYC | Know Your Customer | Customer identification and verification |
| LCR | Liquidity Coverage Ratio | Basel III liquidity metric |
| MLRO | Money Laundering Reporting Officer | Senior compliance officer for AML |
| NSFR | Net Stable Funding Ratio | Basel III funding metric |
| OFAC | Office of Foreign Assets Control | US sanctions authority |
| RTGS | Real-Time Gross Settlement | Immediate payment settlement system |
| SAR | Suspicious Activity Report | Regulatory filing for suspicious transactions |
| SDN | Specially Designated Nationals | OFAC sanctions list |
| SEPA | Single Euro Payments Area | European payment scheme |
| SoD | Segregation of Duties | Control requiring multiple people for sensitive tasks |
| SWIFT | Society for Worldwide Interbank Financial Telecommunication | International payment network |
| UTC | Coordinated Universal Time | Global time standard |

## 3. Business Terms

### 3.1 Entity Definitions

| Term | Definition |
|------|------------|
| BankSubsidiary_TR | Turkish subsidiary entity for local and international payments |
| GroupTreasuryCo | Group-level treasury entity for intercompany and large-value payments |
| Beneficiary | The recipient of a payment |
| Originator | The party initiating a payment request |
| Correspondent Bank | Intermediary bank for international payments |

### 3.2 Payment Terms

| Term | Definition |
|------|------------|
| Buffer | Minimum liquidity reserve that must be maintained |
| Breach | When available balance falls below required buffer |
| Cutoff | Deadline for submitting same-day payments |
| Settlement | Finalization of payment transfer between banks |
| Nostro Account | Bank's account held at a foreign correspondent bank |
| Vostro Account | Account held by a correspondent bank at the local bank |

### 3.3 Status Definitions

| Status | Definition | Allowed Next Status |
|--------|------------|---------------------|
| QUEUED | Payment received, awaiting processing | RELEASED, HOLD, REJECTED |
| PENDING_APPROVAL | Awaiting required approval | RELEASED, HOLD, REJECTED |
| HOLD | Temporarily stopped, requires resolution | RELEASED, REJECTED |
| ON_HOLD | Same as HOLD | RELEASED, REJECTED |
| RELEASED | Approved and sent for settlement | (terminal) |
| REJECTED | Declined, will not be processed | (terminal) |

## 4. Tool Output Fields

### 4.1 Sanctions Screening Response

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| decision | string | Screening decision | "CLEAR", "ESCALATE", "BLOCK" |
| confidence | integer | Confidence percentage (0-100) | 98 |
| match_type | string | Type of match found | "EXACT", "FUZZY_HIGH", "NONE" |
| search_score | float | Azure Search relevance score | 14.627 |
| best_match.uid | string | OFAC unique identifier | "4633" |
| best_match.primary_name | string | Primary name on SDN | "BANK MASKAN" |
| best_match.aka_names | array | Also Known As names | ["MASKAN BANK"] |
| best_match.programs | array | Sanctions programs | ["IRAN", "IRAN-EO13902"] |
| best_match.entity_type | string | Type of sanctioned party | "Entity", "Individual" |
| best_match.remarks | string | Additional OFAC notes | "Address: Tehran, Iran" |
| audit.index | string | Search index used | "idx-ofac-sdn-v1" |
| audit.workflow_run_id | string | Unique workflow execution ID | "08584328..." |
| audit.timestamp_utc | string | ISO8601 timestamp | "2026-01-19T08:10:00.000Z" |
| audit.version | string | Workflow version | "2.1-sms" |

### 4.2 Liquidity Gate Response

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| decision | string | Liquidity decision | "PROCEED", "HOLD", "REJECT" |
| breach | boolean | Whether buffer is breached | true |
| breach_amount | decimal | Shortfall amount if breached | 50000.00 |
| projected_balance | decimal | Balance after payment | 1950000.00 |
| min_buffer | decimal | Required minimum buffer | 2000000.00 |
| headroom | decimal | Available above buffer | -50000.00 (negative = breach) |
| headroom_pct | decimal | Headroom as percentage | -2.5 |
| currency | string | Currency code | "USD" |
| entity | string | Entity identifier | "BankSubsidiary_TR" |
| account_id | string | Account identifier | "ACC-BAN-001" |
| cutoff_time_utc | string | Settlement cutoff | "15:00" |
| before_cutoff | boolean | Whether before cutoff | true |
| alternatives | array | Suggested alternatives | ["delay", "partial", "override"] |
| beneficiary_concentration | object | Concentration metrics | {"pct": 15.2, "rank": 1} |
| anomaly_flags | array | Detected anomalies | ["LARGE_SINGLE_TXN"] |
| audit.run_id | string | Unique execution ID | "LIQ-2026-01-19-001" |
| audit.timestamp_utc | string | ISO8601 timestamp | "2026-01-19T10:25:00.000Z" |
| audit.data_snapshot | object | Point-in-time data used | {...} |

### 4.3 Payment Record Fields (Ledger)

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| txn_id | string | Unique transaction identifier | "TXN-EMRG-001" |
| timestamp_utc | datetime | Payment request timestamp | "2026-01-19 10:25:00" |
| entity | string | Originating entity | "BankSubsidiary_TR" |
| account_id | string | Source account | "ACC-BAN-001" |
| beneficiary_name | string | Recipient name | "ACME Trading LLC" |
| payment_type | string | Payment classification | "URGENT_SUPPLIER" |
| amount | decimal | Payment amount | 250000.00 |
| direction | string | IN or OUT | "OUT" |
| currency | string | Currency code | "USD" |
| status | string | Current status | "QUEUED" |
| alert_flag | string | Any alerts raised | "ANOMALY_DETECTED" |
| channel | string | Payment channel | "SWIFT" |

### 4.4 Buffer Configuration Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| entity | string | Entity identifier | "BankSubsidiary_TR" |
| currency | string | Currency code | "USD" |
| min_buffer | decimal | Minimum required balance | 2000000 |
| cutoff_time_utc | string | Settlement cutoff time | "15:00" |
| description | string | Buffer purpose | "USD nostro buffer for SWIFT" |

### 4.5 Starting Balance Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| entity | string | Entity identifier | "BankSubsidiary_TR" |
| account_id | string | Account identifier | "ACC-BAN-001" |
| currency | string | Currency code | "USD" |
| start_of_day_balance | decimal | Opening balance | 2200000.00 |

## 5. Decision Values

### 5.1 Sanctions Decisions

| Value | Meaning | Required Action |
|-------|---------|-----------------|
| CLEAR | No sanctions match found | Proceed to liquidity check |
| ESCALATE | Potential match, requires review | Hold + Compliance review |
| BLOCK | Confirmed sanctions match | Reject + File report |

### 5.2 Liquidity Decisions

| Value | Meaning | Required Action |
|-------|---------|-----------------|
| PROCEED | No buffer breach | Release payment |
| HOLD | Buffer breach detected | Treasury review required |
| REJECT | Breach + past cutoff | Cannot process today |

### 5.3 Final Payment Decisions

| Value | Meaning | Audit Requirement |
|-------|---------|-------------------|
| RELEASED | Payment sent for settlement | Standard bundle |
| HOLD | Awaiting resolution | Enhanced bundle |
| REJECTED | Payment declined | Enhanced bundle + reason |

## 6. Calculation Formulas

### 6.1 Projected Balance

```
projected_balance = start_of_day_balance
                    + SUM(inflows WHERE timestamp < payment_timestamp)
                    - SUM(outflows WHERE timestamp < payment_timestamp)
                    - payment_amount
```

### 6.2 Headroom

```
headroom = projected_balance - min_buffer
headroom_pct = (headroom / min_buffer) * 100
```

### 6.3 Breach Detection

```
IF projected_balance < min_buffer THEN
    breach = true
    breach_amount = min_buffer - projected_balance
ELSE
    breach = false
    breach_amount = 0
END IF
```

### 6.4 Beneficiary Concentration

```
beneficiary_total = SUM(payments TO beneficiary today)
total_outflows = SUM(all outflows today)
concentration_pct = (beneficiary_total / total_outflows) * 100
```

## 7. Error Codes

### 7.1 System Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| ERR_SANC_UNAVAIL | Sanctions service unavailable | Retry or manual screen |
| ERR_LIQ_UNAVAIL | Liquidity service unavailable | Retry or manual check |
| ERR_DB_CONN | Database connection failed | Contact IT support |
| ERR_TIMEOUT | Service timeout | Retry after delay |
| ERR_INVALID_INPUT | Invalid request parameters | Check input format |

### 7.2 Business Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| BIZ_CUTOFF_MISSED | Past settlement cutoff | Process next business day |
| BIZ_BUFFER_BREACH | Liquidity buffer breached | Treasury review required |
| BIZ_APPROVAL_DENIED | Required approval not granted | Review with approver |
| BIZ_DUPLICATE_TXN | Duplicate transaction detected | Verify intent |

## 8. Data Retention

| Data Type | Retention Period | Legal Basis |
|-----------|------------------|-------------|
| Payment records | 7 years | AML regulations |
| Sanctions screening | 7 years | OFAC requirements |
| Approval records | 7 years | Audit requirements |
| Sanctions cases | Permanent | Regulatory requirement |
| SAR filings | Permanent | FinCEN requirement |
| System logs | 2 years | IT policy |

---

*Document Owner: Data Governance*
*Last Review: 2026-01-01*
*Next Review: 2027-01-01*
