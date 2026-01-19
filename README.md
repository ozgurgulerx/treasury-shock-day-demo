# Treasury Shock Day Demo

**Multi-Agent AI Workflow for Intraday Liquidity & FX Stress Response**

A comprehensive demonstration of Azure AI Foundry capabilities in a banking/treasury operations scenario, showcasing how intelligent agents collaborate to handle crisis situations with full enterprise governance.

---

## Scenario Overview

A macro economic shock event triggers an intraday liquidity crisis combined with FX (foreign exchange) stress. This simulates a realistic "shock day" scenario that treasury operations teams face—where rapid decision-making is required across multiple data sources, forecasting models, and approval workflows.

### The Story

> *It's 9:47 AM. The Federal Reserve just announced an emergency rate hike. Your treasury team has 2 hours to assess $4.2 billion in liquidity exposure across 12 currencies. In the old world, this meant 47 phone calls, 12 spreadsheets, and hoping nothing fell through the cracks.*

**What happens next:**

1. **Trigger Event** — A macro shock is detected (sudden rate announcement, geopolitical event, market flash crash)
2. **Impact Assessment** — Agents assess liquidity positions, FX exposures, and policy compliance
3. **Forecast & Recommendation** — ML models predict cash flow impacts; agents recommend actions
4. **Approval Workflow** — Multi-agent system generates approval pack, routes for authorization
5. **Audit & Compliance** — Complete audit bundle generated with full traceability
6. **Resolution** — Successful crisis response with complete documentation

---

## What This Demo Demonstrates

| Capability | Before (Baseline) | After (With Foundry) |
|------------|-------------------|----------------------|
| Knowledge Retrieval | Single RAG index (WEO RAPTOR) | Foundry IQ: Multi-source KB (WEO + Policies + Fabric + Web) |
| Tool Integration | Manual API calls | Unified MCP Tools Catalog |
| Agent Orchestration | Single agent | Multi-agent workflows with state management |
| Governance | Manual tracking | Foundry Control Plane + AI Gateway |
| Identity | No agent identity | Entra Agent ID with verifiable credentials |
| Model Selection | Fixed model | Model Router (best model per task) |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FOUNDRY CONTROL PLANE                              │
│  (Fleet Visibility | Tracing | Monitoring | Evals | Red Teaming | Controls) │
├─────────────────────────────────────────────────────────────────────────────┤
│                              AI GATEWAY                                      │
│        (Cost/Usage Limits | Model Routing | Policy Enforcement)              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     FOUNDRY AGENT SERVICE                              │  │
│  │                    (Hosted Multi-Agent Workflow)                       │  │
│  │                                                                        │  │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐         │  │
│  │  │ Liquidity  │ │    FX      │ │  Forecast  │ │  Approval  │         │  │
│  │  │   Agent    │ │   Agent    │ │   Agent    │ │   Agent    │   ...   │  │
│  │  │            │ │            │ │            │ │            │         │  │
│  │  │ [Entra ID] │ │ [Entra ID] │ │ [Entra ID] │ │ [Entra ID] │         │  │
│  │  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘         │  │
│  └────────┼──────────────┼──────────────┼──────────────┼────────────────┘  │
│           │              │              │              │                    │
├───────────┴──────────────┴──────────────┴──────────────┴────────────────────┤
│                            KNOWLEDGE LAYER                                   │
│                                                                              │
│             ┌─────────────────────────────────────────────┐                 │
│             │            FOUNDRY IQ KB                     │                 │
│             │  ┌─────────┐ ┌───────────┐ ┌─────────────┐  │                 │
│             │  │   WEO   │ │ Treasury  │ │  Fabric IQ  │  │                 │
│             │  │  Index  │ │ Policies  │ │   (Data)    │  │                 │
│             │  └─────────┘ └───────────┘ └─────────────┘  │                 │
│             └─────────────────────────────────────────────┘                 │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                         MCP TOOLS CATALOG                                    │
│                                                                              │
│   ┌──────────────────┐  ┌────────────────────┐  ┌──────────────────┐       │
│   │   SaaS Tools     │  │  Logic Apps        │  │   ML Models      │       │
│   │  (Morningstar)   │  │  (1,400+ systems)  │  │  (Nixtla/APIM)   │       │
│   └──────────────────┘  └────────────────────┘  └──────────────────┘       │
│                                                                              │
├──────────────────────────────────────────────────────────────────────────────┤
│                         DATA LAYER (FABRIC)                                  │
│                                                                              │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐         │
│   │    Lakehouse     │  │  Semantic Model  │  │ Anomaly Detection│         │
│   │ (Treasury Data)  │  │ (Entities/Rels)  │  │  (Fabric Agent)  │         │
│   └──────────────────┘  └──────────────────┘  └──────────────────┘         │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Components Checklist

### IMPLEMENTED: Sanctions Screening Service

A production-ready OFAC sanctions screening workflow has been implemented as the first operational component of this multi-agent system.

#### What Was Built

| Component | Description | Status |
|-----------|-------------|--------|
| **OFAC SDN Parser** | Extracts 18,557 records from SDN_ENHANCED.xml | ✅ |
| **Azure AI Search Index** | `idx-ofac-sdn-v1` with full-text search | ✅ |
| **Screening Logic App** | `SanctionsScreeningFlow` with CLEAR/ESCALATE/BLOCK decisions | ✅ |
| **Fuzzy Matching** | Catches typos using Lucene `~` operator | ✅ |
| **SMS Notifications** | Real-time alerts via Infobip for all screening results | ✅ |
| **Test Suite** | Automated validation of screening decisions | ✅ |

#### Screening Decision Logic (v2.1 - Fuzzy Matching + SMS)

| Decision | Match Type | Confidence | Trigger |
|----------|------------|------------|---------|
| **BLOCK** | EXACT | 98% | Exact match on primary_name or aka_names |
| **BLOCK** | FUZZY_HIGH | 90% | High-confidence fuzzy match (search score ≥ 8) |
| **ESCALATE** | FUZZY_MEDIUM | 75% | Medium-confidence fuzzy match (score 4-8) |
| **ESCALATE** | PARTIAL | 60% | Low-confidence partial match (score 2-4) |
| **CLEAR** | NONE | 0% | No matches found (score < 2) |

**Fuzzy matching** uses Azure AI Search's Lucene query syntax with `~` operator to catch typos and spelling variations. For example, "BANKE MASKAN" or "BANK MASKAAN" will still match "BANK MASKAN".

#### API Endpoint

```bash
# Screen a name against OFAC SDN list
curl -X POST "https://prod-40.uksouth.logic.azure.com/workflows/..." \
  -H "Content-Type: application/json" \
  -d '{"name": "BANK MASKAN", "context": {"payment_id": "PAY-123"}}'
```

#### Response Format
```json
{
  "decision": "BLOCK",
  "confidence": 98,
  "match_type": "EXACT",
  "match_reason": "Exact match on primary_name or aka_names",
  "search_score": 14.626775,
  "best_match": {
    "uid": "4633",
    "primary_name": "BANK MASKAN",
    "programs": ["IRAN", "IRAN-EO13902"],
    "entity_type": "Entity"
  },
  "input": {
    "name": "BANK MASKAN",
    "normalized_name": "BANK MASKAN",
    "fuzzy_query": "BANK~ AND MASKAN~"
  },
  "notification": {
    "sms_attempted": true,
    "sms_to": "+905322000857",
    "sms_status": "sent"
  },
  "audit": {
    "index": "idx-ofac-sdn-v1",
    "workflow_run_id": "08584328455194303027128363177CU09",
    "timestamp_utc": "2026-01-19T08:10:00.000Z",
    "version": "2.1-sms"
  }
}
```

**SMS Message Format:**
```
SANCTIONS SCREENING [BLOCK] Name: BANK MASKAN | Confidence: 98% | Match: BANK MASKAN | Run: {workflow_id}
```

#### Files Added
```
├── parse_sdn_enhanced.py         # XML parser for OFAC SDN data
├── upload_to_azure_search.py     # Azure Search index uploader
├── sdn_enhanced_records.json     # 18,557 parsed sanctions records
├── test_workflow.py              # Logic App test suite
└── logic-apps/
    └── SanctionsScreeningFlow/
        └── workflow.json         # Logic App definition
```

#### Workflow Internal Architecture (v2.1)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SanctionsScreeningFlow Logic App                     │
│                     (v2.1 - Fuzzy Matching + SMS)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐                                                       │
│  │ HTTP Request │ POST { name, country?, context? }                     │
│  └──────┬───────┘                                                       │
│         ▼                                                               │
│  ┌──────────────────────────────────────┐                              │
│  │ Initialize Variables                  │                              │
│  │ decision="CLEAR", bestScore=0,        │                              │
│  │ matchType="NONE", matchReason="",     │                              │
│  │ searchScore=0, bestMatch={}           │                              │
│  └──────────────────┬───────────────────┘                              │
│                     ▼                                                   │
│  ┌──────────────────────────────────────┐                              │
│  │ Normalize_Name                        │                              │
│  │ toUpper(trim(name))                   │                              │
│  └──────────────────┬───────────────────┘                              │
│                     ▼                                                   │
│  ┌──────────────────────────────────────┐                              │
│  │ Build_Fuzzy_Query                     │                              │
│  │ "BANK MASKAN" → "BANK~ AND MASKAN~"   │                              │
│  └──────────────────┬───────────────────┘                              │
│                     ▼                                                   │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Query_Azure_AI_Search (Lucene Full-Text)                          │  │
│  │ Body: { search: "BANK~ AND MASKAN~",                              │  │
│  │        queryType: "full", top: 10 }                               │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ For_Each_Result (Score-Based Decisions)                           │  │
│  │ ┌──────────────────────────────────────────────────────────────┐ │  │
│  │ │ 1. EXACT match? → BLOCK (98%)                                │ │  │
│  │ │ 2. FUZZY_HIGH (score ≥ 8)? → BLOCK (90%)                     │ │  │
│  │ │ 3. FUZZY_MEDIUM (score ≥ 4)? → ESCALATE (75%)                │ │  │
│  │ │ 4. PARTIAL (score ≥ 2)? → ESCALATE (60%)                     │ │  │
│  │ └──────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Build_SMS_Message                                                 │  │
│  │ "SANCTIONS SCREENING [BLOCK] Name: X | Confidence: Y%..."        │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Send_SMS_Notification (Infobip API)                        ◄─ NEW │  │
│  │ POST https://api.infobip.com/sms/2/text/advanced                  │  │
│  │ → Sends real-time SMS alert to compliance team                    │  │
│  └──────────────────────────────┬───────────────────────────────────┘  │
│                                 ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ HTTP Response (200)                                               │  │
│  │ { decision, confidence, match_type, notification{}, audit{} }    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**External Integrations:**
| Service | Purpose | Status |
|---------|---------|--------|
| Azure AI Search | OFAC SDN index queries | ✅ Active |
| Infobip SMS API | Real-time notifications | ✅ Active |

#### Live Endpoint

**Trigger URL:**
```
https://prod-35.uksouth.logic.azure.com:443/workflows/cc66c376585147c6aab13c262ada26f4/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=R4rI4j2aOC0cxpcU-XYrZlTiPGtL6aV_JTAgJHY1_dU
```

**Quick Test:**
```bash
curl -X POST "https://prod-35.uksouth.logic.azure.com:443/workflows/cc66c376585147c6aab13c262ada26f4/triggers/When_a_HTTP_request_is_received/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2FWhen_a_HTTP_request_is_received%2Frun&sv=1.0&sig=R4rI4j2aOC0cxpcU-XYrZlTiPGtL6aV_JTAgJHY1_dU" \
  -H "Content-Type: application/json" \
  -d '{"name": "BANK MASKAN"}'
```

#### Test Results (v2.1)

| Test Input | Match Type | Decision | Confidence | SMS | Status |
|------------|------------|----------|------------|-----|--------|
| BANK MASKAN | EXACT | BLOCK | 98% | ✅ Sent | ✅ |
| TANCHON COMMERCIAL BANK | EXACT | BLOCK | 98% | ✅ Sent | ✅ |
| AEROCARIBBEAN AIRLINES | EXACT | BLOCK | 98% | ✅ Sent | ✅ |
| **BANKE MASKAN** (typo) | FUZZY_HIGH | BLOCK | 90% | ✅ Sent | ✅ |
| **BANK MASKAAN** (typo) | FUZZY_HIGH | BLOCK | 90% | ✅ Sent | ✅ |
| **BNKA MASKAN** (typo) | FUZZY_HIGH | BLOCK | 90% | ✅ Sent | ✅ |
| Housing Bank | EXACT (AKA) | BLOCK | 98% | ✅ Sent | ✅ |
| Microsoft Corporation | NONE | CLEAR | 0% | ✅ Sent | ✅ |
| Amazon Web Services | NONE | CLEAR | 0% | ✅ Sent | ✅ |

**Run automated tests:**
```bash
source .venv/bin/activate
python test_workflow.py
```

**Features:**
- Fuzzy matching catches typos and spelling variations
- SMS notifications sent for ALL decisions (BLOCK, ESCALATE, CLEAR)
- Non-blocking SMS: workflow completes even if SMS fails

#### Integration with Demo Phases

This workflow is the **first working component** of the multi-agent system:

| Demo Phase | Role of Sanctions Screening |
|------------|----------------------------|
| Phase 3: Tool Integration | ✅ **First Logic App exposed as callable tool** |
| Phase 4: Multi-Agent | Sanctions Agent will call this for counterparty screening |
| Phase 6: Finale | Evidence bundle includes screening audit trail |

**Next Steps to Full Integration:**
1. Wrap as MCP tool or Semantic Kernel plugin
2. Create Sanctions Agent that calls this workflow
3. Integrate into Treasury Shock Coordinator orchestration

---

### A) Foundry Runtime & Governance

| Component | Description | Status |
|-----------|-------------|--------|
| **Foundry Agent Service** | Hosted agents environment (preview) — no infra/container management | ⬜ |
| **Multi-Agent Workflows** | Visual designer or code-first API; long-running, stateful, recovery/debugging | ⬜ |
| **Agent Memory** | (Optional) Persistent preferences/history across sessions | ⬜ |
| **Foundry Control Plane** | Fleet visibility, tracing, monitoring, evals, red teaming, agent controls | ⬜ |
| **AI Gateway** | Cost/usage limits for models, agents, MCP tools | ⬜ |
| **Defender + Purview** | Security and compliance integrations (narrate if not fully configured) | ⬜ |
| **Entra Agent ID** | Identity blueprint, registry, lifecycle governance, conditional access | ⬜ |

### B) Knowledge Layer

| Component | Description | Status |
|-----------|-------------|--------|
| **Baseline RAG** | WEO RAPTOR index in Azure AI Search (single source) | ✅ |
| **Foundry IQ Knowledge Base** | Multi-source KB: WEO + Treasury Policies + Fabric IQ + Web | ⬜ |

**Demo Goal**: Show before/after answer quality improvement when enabling Foundry IQ with agentic retrieval.

### C) Data Layer (Microsoft Fabric)

| Component | Description | Status |
|-----------|-------------|--------|
| **Lakehouse/Warehouse** | Synthetic treasury datasets | ⬜ |
| **Semantic Model** | Entities + relationships for treasury operations | ⬜ |
| **Fabric Data Agent** | Anomaly detection capabilities | ⬜ |

### D) Tools Layer (MCP)

| Tool Type | Implementation | Status |
|-----------|----------------|--------|
| **Sanctions Screening** | OFAC SDN screening via Logic App (SanctionsScreeningFlow) | ✅ |
| **SaaS Connector** | Morningstar market data provider (or alternative) via MCP | ⬜ |
| **Logic Apps Connector** | Expose Logic Apps flows as MCP tools (access to 1,400+ systems) | ⬜ |
| **ML Model** | Nixtla time series prediction exposed via API Management as MCP | ⬜ |

---

## The Agents

### Primary Agents

| Agent | Role | Tools | Knowledge |
|-------|------|-------|-----------|
| **Liquidity Assessment Agent** | Analyzes current liquidity positions, identifies stress points | Fabric Data Agent, Treasury DB | Foundry IQ (policies + data) |
| **FX Exposure Agent** | Evaluates foreign exchange exposures and hedging positions | Morningstar, FX calculators | Foundry IQ (FX policies) |
| **Forecast Agent** | Predicts cash flow impacts using ML models | Nixtla time series | Historical data, WEO |
| **Anomaly Detection Agent** | Identifies unusual patterns in treasury data | Fabric Anomaly Detection | Real-time transactions |
| **Policy Compliance Agent** | Validates all recommendations against treasury policies | Policy search | Treasury Policy Pack |
| **Sanctions Screening Agent** | Screens counterparties against OFAC SDN list | SanctionsScreeningFlow | idx-ofac-sdn-v1 |
| **Approval Workflow Agent** | Orchestrates approval routing and audit trail generation | Logic Apps, Email/Teams | Approval matrices |

### Orchestrator

| Agent | Role |
|-------|------|
| **Treasury Shock Coordinator** | Master agent that orchestrates the workflow, delegates to specialized agents, aggregates results into final approval pack |

---

## Demo Flow

### Phase 1: Baseline Demonstration
- Show existing WEO RAPTOR RAG index
- Query single-source RAG with treasury question
- Highlight limitations (single source, no policy context)

### Phase 2: Foundry IQ Upgrade
- Connect additional sources to Foundry IQ
- Same query returns enriched, multi-source answer
- Demonstrate agentic retrieval capabilities

### Phase 3: Tool Integration
- Add Morningstar SaaS tool via MCP
- Add Logic Apps connector as MCP tool
- Expose Nixtla forecast model via API Management
- Show unified MCP tools catalog

### Phase 4: Multi-Agent Workflow
- Trigger macro shock event
- Liquidity Agent assesses positions
- FX Agent evaluates exposures
- Forecast Agent predicts impacts
- Anomaly Agent flags unusual patterns
- Policy Agent validates recommendations

### Phase 5: Governance & Identity
- Show Foundry Control Plane dashboard
- Demonstrate AI Gateway cost/usage tracking
- Show Entra Agent ID credentials
- (Optional) Model Router in action

### Phase 6: Finale
- Approval Agent generates approval pack
- Route through approval workflow
- Generate complete audit bundle
- **Success celebration**

---

## Key Features Showcased

| Feature | Description | Impact |
|---------|-------------|--------|
| **Foundry Agent Service** | Hosted, managed agent runtime with no infrastructure management | High |
| **Multi-Agent Workflows** | Visual + code-first orchestration with state management | High |
| **Foundry IQ** | Unified knowledge base across heterogeneous sources | Very High |
| **MCP Tools Catalog** | Standardized tool integration (SaaS, Logic Apps, ML) | High |
| **Foundry Control Plane** | Enterprise governance, monitoring, and controls | High |
| **AI Gateway** | Cost/usage management across all AI operations | Medium |
| **Entra Agent ID** | Verifiable agent identity with lifecycle governance | High |
| **Model Router** | Intelligent model selection per task | Very High |

---

## Repository Structure

```
treasury-shock-day-demo/
├── README.md                       # This documentation
├── PLAN.md                         # Implementation planning notes
│
├── # ══════════════════════════════════════════════════════════════
├── # SANCTIONS SCREENING (IMPLEMENTED)
├── # ══════════════════════════════════════════════════════════════
├── SDN_ENHANCED.xml                # OFAC source data (gitignored, 100MB)
├── sdn_enhanced_records.json       # Parsed records (18,557 entries)
├── parse_sdn_enhanced.py           # XML parser for OFAC SDN data
├── upload_to_azure_search.py       # Azure AI Search uploader
├── test_workflow.py                # Logic App test suite
├── logic-apps/
│   ├── SanctionsScreeningFlow/
│   │   └── workflow.json           # Logic App workflow definition
│   ├── host.json                   # Logic Apps runtime config
│   ├── deploy.sh                   # Bash deployment script
│   └── deploy_workflow.py          # Python deployment helper
│
├── # ══════════════════════════════════════════════════════════════
├── # PLANNED COMPONENTS
├── # ══════════════════════════════════════════════════════════════
├── agents/                         # (Planned) Agent implementations
│   ├── liquidity-agent/
│   ├── fx-agent/
│   ├── forecast-agent/
│   ├── anomaly-agent/
│   ├── policy-agent/
│   ├── sanctions-agent/            # Will use SanctionsScreeningFlow
│   ├── approval-agent/
│   └── coordinator-agent/
├── knowledge/                      # (Planned) Knowledge bases
│   ├── weo-index/
│   ├── policies/
│   └── foundry-iq-config/
├── data/                           # (Planned) Data assets
│   ├── synthetic-treasury/
│   └── fabric-semantic-model/
├── tools/                          # (Planned) MCP tool wrappers
│   ├── mcp-sanctions/              # Wrap SanctionsScreeningFlow as MCP
│   ├── mcp-morningstar/
│   ├── mcp-logicapps/
│   └── mcp-nixtla/
├── workflows/                      # (Planned) Multi-agent workflows
│   └── shock-day-workflow/
├── infrastructure/                 # (Planned) IaC templates
│   ├── bicep/
│   └── terraform/
│
├── # ══════════════════════════════════════════════════════════════
├── # CONFIGURATION
├── # ══════════════════════════════════════════════════════════════
├── .env                            # Azure credentials (gitignored)
├── .gitignore                      # Git ignore rules
└── .venv/                          # Python virtual environment (gitignored)
```

---

## Azure Resources Deployed

| Resource | Name | Location | Purpose |
|----------|------|----------|---------|
| AI Search | chatops-ozguler | UK South | Hosts idx-ofac-sdn-v1 index |
| Search Index | idx-ofac-sdn-v1 | - | 18,557 OFAC SDN records |
| Logic App | SanctionsScreeningFlow | UK South | Screening workflow |
| Storage | stsanctionsscreen01 | UK South | Logic App state storage |
| App Service Plan | asp-sanctions-screening | UK South | Logic App hosting |

---

## Prerequisites

### Azure Services Required
- Azure subscription with appropriate permissions
- Azure AI Foundry access (preview features enabled)
- Azure AI Search instance
- Microsoft Fabric workspace
- Azure API Management instance
- Azure Logic Apps
- Microsoft Entra ID (for Agent ID)

### Data & Models
- WEO RAPTOR index (existing)
- Synthetic treasury dataset
- Treasury policy documents
- Nixtla time series model

### External Services
- Morningstar API access (or alternative market data provider)

---

## Getting Started

```bash
# Clone the repository
git clone <repo-url>
cd treasury-shock-day-demo

# Run setup script (configures Azure resources)
./scripts/setup.sh

# Reset demo to initial state before presenting
./scripts/demo-reset.sh
```

---

## License

[Specify license]

---

*Demo Target: Azure AI Foundry — Treasury Shock Day Demonstration*
