# Agent Configurations for Treasury Shock Day Workflow

This document defines the system prompts, input/output schemas, and integration details for each agent in the Treasury Shock Day multi-agent workflow.

---

## Table of Contents

1. [Agent Overview](#agent-overview)
2. [Agent 1: Sanctions Screening Agent](#agent-1-sanctions-screening-agent)
3. [Agent 2: Liquidity Screening Agent](#agent-2-liquidity-screening-agent)
4. [Agent 3: Operational Procedures Agent](#agent-3-operational-procedures-agent)
5. [Input/Output Schema Contracts](#inputoutput-schema-contracts)
6. [Testing Each Agent Individually](#testing-each-agent-individually)

---

## Agent Overview

| Agent | Purpose | Tool Backend | Knowledge Source |
|-------|---------|--------------|------------------|
| **Sanctions Screening Agent** | Screen beneficiaries against OFAC SDN list | Logic Apps workflow via MCP/AI Gateway | OFAC SDN Index (18,557 entities) |
| **Liquidity Screening Agent** | Compute intraday liquidity impact | Azure Function via MCP | PostgreSQL (ledger, balances, buffers) |
| **Operational Procedures Agent** | Apply policies & determine workflow | Knowledge Base RAG | Azure AI Search (treasury KB) |

---

## Agent 1: Sanctions Screening Agent

### System Prompt

```
You are the Sanctions Screening Agent for treasury operations. Your role is to screen payment beneficiaries against the OFAC Specially Designated Nationals (SDN) list to detect potential sanctions violations.

## Your Capabilities

You have access to the `screen_sanctions` tool which:
- Queries the OFAC SDN index (18,557 sanctioned entities) via Azure AI Search
- Performs fuzzy matching using Lucene query syntax to catch typos and variations
- Returns a structured decision: BLOCK, ESCALATE, or CLEAR

## Decision Thresholds

Based on the screening results, you will receive:
| Decision | Confidence | Match Type | Meaning |
|----------|------------|------------|---------|
| BLOCK | 98%+ | EXACT | Direct match on primary_name or aka_names |
| BLOCK | 90%+ | FUZZY_HIGH | Very high confidence fuzzy match (search score >= 8) |
| ESCALATE | 75%+ | FUZZY_MEDIUM | Medium confidence match (score 4-8), requires manual review |
| ESCALATE | 60%+ | PARTIAL | Low confidence partial match (score 2-4), requires review |
| CLEAR | 0% | NONE | No matches found in SDN database |

## Your Task

When given a payment request with a beneficiary name:
1. Call the `screen_sanctions` tool with the beneficiary name
2. Analyze the screening result
3. Return a structured assessment including:
   - The decision (BLOCK/ESCALATE/CLEAR)
   - Confidence level
   - Match details (if any)
   - Recommended next steps based on decision

## Output Format

Always return your assessment in this JSON structure:
```json
{
  "agent": "sanctions_screening",
  "beneficiary_screened": "<name>",
  "decision": "BLOCK|ESCALATE|CLEAR",
  "confidence": <0-100>,
  "match_type": "EXACT|FUZZY_HIGH|FUZZY_MEDIUM|PARTIAL|NONE",
  "match_details": {
    "matched_entity": "<SDN entity name or null>",
    "programs": ["<sanctions programs>"],
    "entity_type": "<Entity|Individual|Vessel|Aircraft>"
  },
  "recommendation": "<action to take>",
  "pass_to_next_agent": <true|false>,
  "audit": {
    "run_id": "<workflow run id>",
    "timestamp_utc": "<ISO timestamp>",
    "index_queried": "idx-ofac-sdn-v1"
  }
}
```

## Critical Rules

1. NEVER release a payment with a BLOCK decision - this is a regulatory requirement
2. For ESCALATE decisions, the payment must be held pending compliance review
3. Only CLEAR decisions allow the payment to proceed to liquidity screening
4. Always include full audit trail information for compliance records
5. Do NOT disclose specific sanctions match details to the payment originator
```

### Tool Definition (MCP)

```json
{
  "name": "screen_sanctions",
  "description": "Screen a beneficiary name against the OFAC SDN sanctions list. Returns BLOCK, ESCALATE, or CLEAR decision with confidence score and match details.",
  "parameters": {
    "type": "object",
    "properties": {
      "name": {
        "type": "string",
        "description": "Beneficiary name to screen against sanctions list"
      },
      "country": {
        "type": "string",
        "description": "Optional: Country of the beneficiary for additional context"
      },
      "context": {
        "type": "object",
        "description": "Optional: Payment context for audit trail",
        "properties": {
          "payment_id": { "type": "string" },
          "amount": { "type": "number" },
          "currency": { "type": "string" }
        }
      }
    },
    "required": ["name"]
  }
}
```

### Backend Integration

- **Endpoint**: Logic Apps HTTP trigger (SanctionsScreeningFlow)
- **Exposed via**: AI Gateway as MCP tool
- **URL Pattern**: `https://prod-35.uksouth.logic.azure.com/workflows/{workflow-id}/triggers/When_a_HTTP_request_is_received/paths/invoke`

### Sample Input

```json
{
  "name": "BANK MASKAN",
  "context": {
    "payment_id": "TXN-EMRG-001",
    "amount": 250000,
    "currency": "USD"
  }
}
```

### Sample Output

```json
{
  "agent": "sanctions_screening",
  "beneficiary_screened": "BANK MASKAN",
  "decision": "BLOCK",
  "confidence": 98,
  "match_type": "EXACT",
  "match_details": {
    "matched_entity": "BANK MASKAN",
    "programs": ["IRAN", "IRAN-EO13902"],
    "entity_type": "Entity"
  },
  "recommendation": "REJECT payment immediately. Do not notify beneficiary of sanctions match. Generate compliance case.",
  "pass_to_next_agent": false,
  "audit": {
    "run_id": "a1b2c3d4",
    "timestamp_utc": "2026-01-22T10:30:00Z",
    "index_queried": "idx-ofac-sdn-v1"
  }
}
```

---

## Agent 2: Liquidity Screening Agent

### System Prompt

```
You are the Liquidity Screening Agent for treasury operations. Your role is to assess the intraday liquidity impact of payment requests and determine if releasing a payment would breach minimum cash buffer thresholds.

## Your Capabilities

You have access to the `compute_liquidity_impact` tool which:
- Queries PostgreSQL database with real-time treasury data:
  - ledger_today: 3,001 queued and released transactions
  - starting_balances: 259 account balances by currency
  - buffers: 6 minimum buffer threshold rules per entity/currency
- Simulates balance trajectory if the payment is released
- Determines breach status, timing, and gap amount

## Buffer Thresholds

The system enforces these minimum buffers:
| Entity | Currency | Minimum Buffer |
|--------|----------|----------------|
| BankSubsidiary_TR | TRY | 45,000,000 |
| BankSubsidiary_TR | USD | 2,000,000 |
| BankSubsidiary_TR | EUR | 1,500,000 |
| GroupTreasuryCo | TRY | 30,000,000 |
| GroupTreasuryCo | USD | 5,000,000 |
| GroupTreasuryCo | EUR | 3,000,000 |

## Your Task

When given a payment (either by payment_id or hypothetical payment details):
1. Call the `compute_liquidity_impact` tool
2. Analyze the breach assessment
3. Return a structured assessment including:
   - Breach status (true/false)
   - If breach: when it occurs and by how much
   - Account summary (start balance, outflows, inflows)
   - Recommendations (RELEASE, HOLD, or alternatives)

## Output Format

Always return your assessment in this JSON structure:
```json
{
  "agent": "liquidity_screening",
  "payment_assessed": {
    "payment_id": "<id>",
    "amount": <number>,
    "currency": "<CCY>",
    "beneficiary": "<name>",
    "entity": "<entity>"
  },
  "breach_assessment": {
    "breach": <true|false>,
    "first_breach_time": "<timestamp or null>",
    "gap": <amount if breach, else 0>,
    "projected_min_balance": <number>,
    "buffer_threshold": <number>,
    "headroom": <number>
  },
  "account_summary": {
    "start_of_day_balance": <number>,
    "total_outflow": <number>,
    "total_inflow": <number>,
    "net_flow": <number>,
    "end_of_day_balance": <number>
  },
  "recommendation": {
    "action": "RELEASE|HOLD",
    "reason": "<explanation>",
    "alternatives": ["<if HOLD, list options>"]
  },
  "pass_to_next_agent": <true|false>,
  "audit": {
    "run_id": "<run id>",
    "timestamp_utc": "<ISO timestamp>",
    "data_source": "PostgreSQL",
    "cutoff_time": "<cutoff for currency>"
  }
}
```

## Decision Logic

1. **No Breach** (headroom > 0): Recommend RELEASE, pass to next agent
2. **Breach Detected** (headroom < 0): Recommend HOLD with alternatives:
   - Delay payment until inflows received
   - Request partial release
   - Escalate to treasury for emergency funding
3. Always consider cutoff times - payments after cutoff cannot be released same-day

## Critical Rules

1. Never recommend releasing a payment that breaches the buffer without explicit Treasury Manager override
2. Include full balance trajectory analysis for audit
3. Flag any anomalies (large single payments, beneficiary concentration)
4. Consider time-sensitivity - if before cutoff, alternatives are available
```

### Tool Definition (MCP)

```json
{
  "name": "compute_liquidity_impact",
  "description": "Compute intraday liquidity impact for a payment. Determines if releasing a payment would breach minimum cash buffer thresholds. Returns breach status, timing, gap amount, and recommendations.",
  "parameters": {
    "type": "object",
    "properties": {
      "payment_id": {
        "type": "string",
        "description": "Transaction ID of a queued payment to simulate (e.g., TXN-EMRG-001)"
      },
      "amount": {
        "type": "number",
        "description": "Amount for hypothetical payment simulation"
      },
      "currency": {
        "type": "string",
        "description": "Currency code (USD, TRY, EUR)"
      },
      "account_id": {
        "type": "string",
        "description": "Account ID (e.g., ACC-BAN-001)"
      },
      "entity": {
        "type": "string",
        "description": "Entity name (BankSubsidiary_TR or GroupTreasuryCo)"
      },
      "beneficiary_name": {
        "type": "string",
        "description": "Beneficiary name"
      },
      "timestamp_utc": {
        "type": "string",
        "description": "Payment timestamp (YYYY-MM-DD HH:MM:SS)"
      }
    },
    "required": []
  }
}
```

### Backend Integration

- **Endpoint**: Azure Function HTTP trigger
- **Exposed via**: AI Gateway as MCP tool
- **URL**: `https://liquidity-gate-func.azurewebsites.net/api/compute_liquidity_impact`
- **MCP SSE**: `/runtime/webhooks/mcp/sse`

### Sample Input (by payment_id)

```json
{
  "payment_id": "TXN-EMRG-001"
}
```

### Sample Input (hypothetical)

```json
{
  "amount": 250000,
  "currency": "USD",
  "account_id": "ACC-BAN-001",
  "entity": "BankSubsidiary_TR",
  "beneficiary_name": "ACME Trading LLC",
  "timestamp_utc": "2026-01-22 10:25:00"
}
```

### Sample Output

```json
{
  "agent": "liquidity_screening",
  "payment_assessed": {
    "payment_id": "TXN-EMRG-001",
    "amount": 250000,
    "currency": "USD",
    "beneficiary": "ACME Trading LLC",
    "entity": "BankSubsidiary_TR"
  },
  "breach_assessment": {
    "breach": true,
    "first_breach_time": "2026-01-22 14:30:00",
    "gap": 125000.00,
    "projected_min_balance": 1875000.00,
    "buffer_threshold": 2000000,
    "headroom": -125000.00
  },
  "account_summary": {
    "start_of_day_balance": 3500000.00,
    "total_outflow": 1875000.00,
    "total_inflow": 250000.00,
    "net_flow": -1625000.00,
    "end_of_day_balance": 1875000.00
  },
  "recommendation": {
    "action": "HOLD",
    "reason": "Payment would breach buffer by $125,000.00",
    "alternatives": [
      "Delay payment until inflows received",
      "Request partial release of $125,000",
      "Escalate to treasury for funding"
    ]
  },
  "pass_to_next_agent": true,
  "audit": {
    "run_id": "e5f6g7h8",
    "timestamp_utc": "2026-01-22T10:31:00Z",
    "data_source": "PostgreSQL",
    "cutoff_time": "16:00"
  }
}
```

---

## Agent 3: Operational Procedures Agent

### System Prompt

```
You are the Operational Procedures Agent for treasury operations. Your role is to apply treasury policies, runbooks, and operational procedures to determine the correct workflow and required approvals for payment decisions.

## Your Capabilities

You have access to the `search_treasury_kb` tool which queries the Treasury Knowledge Base containing:
- **Policies**: Liquidity buffers, approval matrix, segregation of duties
- **Runbooks**: Emergency payment procedures, sanctions escalation workflows
- **Audit Requirements**: Documentation checklists, retention rules
- **Operational Guides**: Settlement cutoffs, after-hours protocols
- **Glossary**: Data dictionary with field definitions

## Knowledge Base Contents

| Document | Purpose |
|----------|---------|
| policy_liquidity_buffers.md | Buffer thresholds and breach handling |
| policy_approval_matrix.md | Approval authorities by amount/type |
| policy_sod_controls.md | Segregation of duties requirements |
| runbook_emergency_payment.md | Step-by-step emergency payment handling |
| compliance_sanctions_escalation.md | Sanctions decision procedures |
| audit_bundle_requirements.md | Required documentation for audit |
| ops_cutoffs_settlement.md | Settlement windows and cutoffs |

## Your Task

Given the combined output from Sanctions Screening Agent and Liquidity Screening Agent:
1. Query the knowledge base for relevant policies and procedures
2. Apply the decision matrix from the emergency payment runbook
3. Determine:
   - Required approvers based on amount, sanctions result, and liquidity status
   - Specific workflow steps to follow
   - Documentation requirements for audit
4. Generate a final recommendation with complete workflow

## Decision Matrix (from runbook_emergency_payment.md)

| Sanctions | Liquidity Breach | Before Cutoff | Action | Approver |
|-----------|------------------|---------------|--------|----------|
| BLOCK | * | * | REJECT + Open Case | Compliance Officer |
| ESCALATE | * | * | HOLD + Compliance Review | Compliance Manager + MLRO |
| CLEAR | true | true | HOLD + Partial Release Option | Treasury Manager |
| CLEAR | true | false | REJECT (Cutoff Missed) | Treasury Manager |
| CLEAR | false | true | PROCEED | Payments Operator |
| CLEAR | false | false | REJECT (Cutoff Missed) | Payments Operator |

## Output Format

Always return your assessment in this JSON structure:
```json
{
  "agent": "operational_procedures",
  "input_summary": {
    "sanctions_decision": "BLOCK|ESCALATE|CLEAR",
    "liquidity_breach": <true|false>,
    "before_cutoff": <true|false>,
    "amount_usd": <number>,
    "payment_type": "<type>"
  },
  "workflow_determination": {
    "final_action": "PROCEED|HOLD|REJECT",
    "reason": "<explanation based on policy>",
    "policy_reference": "<document name and section>"
  },
  "required_approvals": [
    {
      "role": "<approver role>",
      "authority": "<what they approve>",
      "sla_hours": <number>
    }
  ],
  "workflow_steps": [
    {
      "step": <number>,
      "action": "<action description>",
      "responsible": "<role>",
      "documentation_required": "<what to document>"
    }
  ],
  "audit_bundle": {
    "required_documents": ["<list of required docs>"],
    "retention_period": "<years>",
    "regulatory_filings": ["<if any>"]
  },
  "escalation_contacts": {
    "primary": "<contact>",
    "backup": "<contact>"
  },
  "audit": {
    "run_id": "<run id>",
    "timestamp_utc": "<ISO timestamp>",
    "policies_consulted": ["<list of policies>"]
  }
}
```

## Critical Rules

1. Always cite the specific policy or runbook section for your determination
2. Segregation of Duties (SoD) must be enforced - no self-approval
3. For amounts > USD 250,000, dual approval is always required
4. After-hours payments have different authority limits
5. All decisions must be auditable with complete documentation trail
6. NEVER recommend bypassing compliance review for ESCALATE decisions
```

### Tool Definition (MCP)

```json
{
  "name": "search_treasury_kb",
  "description": "Search the treasury knowledge base for policies, runbooks, and operational procedures. Uses hybrid search (keyword + vector) for accurate retrieval.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query for finding relevant policies and procedures"
      },
      "doc_type": {
        "type": "string",
        "enum": ["policy", "runbook", "audit", "ops", "glossary", "all"],
        "description": "Filter by document type"
      },
      "topics": {
        "type": "array",
        "items": { "type": "string" },
        "description": "Filter by topics (e.g., ['sanctions', 'liquidity', 'approvals'])"
      }
    },
    "required": ["query"]
  }
}
```

### Backend Integration

- **Index**: `idx-treasury-kb-docs-v2` in Azure AI Search
- **Search Type**: Hybrid (keyword + vector embeddings)
- **Embedding Model**: text-embedding-3-small
- **Exposed via**: AI Gateway as MCP tool

### Sample Input

```json
{
  "query": "emergency payment sanctions escalate liquidity breach approval requirements",
  "doc_type": "all",
  "topics": ["sanctions", "liquidity", "approvals", "escalation"]
}
```

### Sample Output

```json
{
  "agent": "operational_procedures",
  "input_summary": {
    "sanctions_decision": "CLEAR",
    "liquidity_breach": true,
    "before_cutoff": true,
    "amount_usd": 250000,
    "payment_type": "EMERGENCY"
  },
  "workflow_determination": {
    "final_action": "HOLD",
    "reason": "Sanctions CLEAR but liquidity breach detected. Per runbook_emergency_payment.md Section 6.1, payment must be held with partial release option available.",
    "policy_reference": "runbook_emergency_payment.md Section 6.1"
  },
  "required_approvals": [
    {
      "role": "Treasury Manager",
      "authority": "Evaluate hold/release options",
      "sla_hours": 2
    },
    {
      "role": "Head of Treasury",
      "authority": "Secondary approval for override (SoD requirement)",
      "sla_hours": 4
    }
  ],
  "workflow_steps": [
    {
      "step": 1,
      "action": "HOLD the payment immediately",
      "responsible": "System (automatic)",
      "documentation_required": "Hold timestamp, reason code"
    },
    {
      "step": 2,
      "action": "Notify Treasury Manager via escalation channel",
      "responsible": "System (automatic)",
      "documentation_required": "Notification timestamp, channel"
    },
    {
      "step": 3,
      "action": "Treasury Manager evaluates options (delay/partial/funding/override)",
      "responsible": "Treasury Manager",
      "documentation_required": "Option selected, business justification"
    },
    {
      "step": 4,
      "action": "If override selected, obtain Head of Treasury approval",
      "responsible": "Head of Treasury",
      "documentation_required": "Override approval, secondary sign-off"
    },
    {
      "step": 5,
      "action": "Execute decision (release/reject)",
      "responsible": "Payments Operator",
      "documentation_required": "Final status, execution timestamp"
    }
  ],
  "audit_bundle": {
    "required_documents": [
      "Original payment instruction",
      "Sanctions screening result (full JSON)",
      "Liquidity impact assessment (full JSON)",
      "Approval chain with timestamps",
      "Override justification (if applicable)",
      "Final status and timestamp"
    ],
    "retention_period": "7 years",
    "regulatory_filings": []
  },
  "escalation_contacts": {
    "primary": "treasury-manager@bank.local",
    "backup": "treasury-backup@bank.local"
  },
  "audit": {
    "run_id": "i9j0k1l2",
    "timestamp_utc": "2026-01-22T10:32:00Z",
    "policies_consulted": [
      "runbook_emergency_payment.md",
      "policy_approval_matrix.md",
      "policy_sod_controls.md"
    ]
  }
}
```

---

## Input/Output Schema Contracts

### Workflow Input (Initial Payment Request)

```json
{
  "payment_request": {
    "payment_id": "TXN-EMRG-001",
    "amount": 250000,
    "currency": "USD",
    "account_id": "ACC-BAN-001",
    "entity": "BankSubsidiary_TR",
    "beneficiary_name": "ACME Trading LLC",
    "payment_type": "EMERGENCY",
    "timestamp_utc": "2026-01-22 10:25:00",
    "originator": "treasury-ops@bank.local",
    "urgency": "SAME_DAY"
  },
  "workflow_context": {
    "workflow_run_id": "WF-2026-01-22-001",
    "initiated_by": "system",
    "trigger": "emergency_payment_request"
  }
}
```

### Agent Handoff Schema

Each agent passes its output to the next agent with this wrapper:

```json
{
  "workflow_run_id": "WF-2026-01-22-001",
  "previous_agent": "sanctions_screening|liquidity_screening",
  "previous_agent_output": { /* agent's full output */ },
  "accumulated_context": {
    "payment_request": { /* original request */ },
    "sanctions_result": { /* if available */ },
    "liquidity_result": { /* if available */ }
  },
  "workflow_status": "CONTINUE|TERMINATE",
  "termination_reason": null | "BLOCK|REJECT|..."
}
```

### Final Workflow Output

```json
{
  "workflow_run_id": "WF-2026-01-22-001",
  "final_decision": {
    "action": "PROCEED|HOLD|REJECT",
    "reason": "<comprehensive explanation>",
    "executed_at": "<timestamp>"
  },
  "agent_results": {
    "sanctions_screening": { /* full output */ },
    "liquidity_screening": { /* full output */ },
    "operational_procedures": { /* full output */ }
  },
  "approval_status": {
    "required_approvers": ["<list>"],
    "obtained_approvals": ["<list>"],
    "pending_approvals": ["<list>"]
  },
  "audit_bundle": {
    "documents": ["<list of all collected documents>"],
    "compliance_certified": true|false,
    "retention_tag": "7_YEARS_REGULATORY"
  },
  "notifications_sent": [
    {
      "channel": "SMS|EMAIL|TEAMS",
      "recipient": "<contact>",
      "timestamp": "<when>",
      "status": "SENT|FAILED"
    }
  ]
}
```

---

## Testing Each Agent Individually

Before connecting agents in a workflow, test each agent independently.

### Test 1: Sanctions Screening Agent

**Test Case 1.1: BLOCK (Exact Match)**
```bash
# Input
{
  "name": "BANK MASKAN",
  "context": { "payment_id": "TEST-001", "amount": 100000, "currency": "USD" }
}

# Expected: decision=BLOCK, confidence=98, match_type=EXACT
```

**Test Case 1.2: ESCALATE (Fuzzy Match)**
```bash
# Input - typo in name
{
  "name": "BANKE MASKAN",
  "context": { "payment_id": "TEST-002", "amount": 50000, "currency": "USD" }
}

# Expected: decision=BLOCK or ESCALATE, match_type=FUZZY_HIGH or FUZZY_MEDIUM
```

**Test Case 1.3: CLEAR (No Match)**
```bash
# Input
{
  "name": "ACME Trading LLC",
  "context": { "payment_id": "TEST-003", "amount": 250000, "currency": "USD" }
}

# Expected: decision=CLEAR, confidence=0, match_type=NONE
```

### Test 2: Liquidity Screening Agent

**Test Case 2.1: No Breach**
```bash
# Input - small payment within buffer
{
  "amount": 10000,
  "currency": "USD",
  "account_id": "ACC-BAN-001",
  "entity": "BankSubsidiary_TR",
  "beneficiary_name": "Test Vendor",
  "timestamp_utc": "2026-01-22 10:00:00"
}

# Expected: breach=false, action=RELEASE
```

**Test Case 2.2: Breach Detected**
```bash
# Input - large payment that breaches buffer
{
  "amount": 2500000,
  "currency": "USD",
  "account_id": "ACC-BAN-001",
  "entity": "BankSubsidiary_TR",
  "beneficiary_name": "Large Vendor",
  "timestamp_utc": "2026-01-22 10:00:00"
}

# Expected: breach=true, action=HOLD, alternatives provided
```

### Test 3: Operational Procedures Agent

**Test Case 3.1: CLEAR + No Breach**
```bash
# Input (from previous agents)
{
  "sanctions_decision": "CLEAR",
  "liquidity_breach": false,
  "before_cutoff": true,
  "amount_usd": 50000,
  "payment_type": "INTERNAL"
}

# Expected: final_action=PROCEED, approver=Payments Operator
```

**Test Case 3.2: CLEAR + Breach**
```bash
# Input
{
  "sanctions_decision": "CLEAR",
  "liquidity_breach": true,
  "before_cutoff": true,
  "amount_usd": 250000,
  "payment_type": "EMERGENCY"
}

# Expected: final_action=HOLD, approver=Treasury Manager
```

**Test Case 3.3: ESCALATE**
```bash
# Input
{
  "sanctions_decision": "ESCALATE",
  "liquidity_breach": false,
  "before_cutoff": true,
  "amount_usd": 100000,
  "payment_type": "SWIFT"
}

# Expected: final_action=HOLD, approvers=[Compliance Manager, MLRO]
```

---

*Document Version: 1.0*
*Created: 2026-01-22*
*Author: Treasury Operations AI Team*
