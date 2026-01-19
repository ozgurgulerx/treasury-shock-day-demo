# README Update Plan: Treasury Shock Day Demo

## Overview

This plan outlines the comprehensive update to the README.md file for the Treasury Shock Day Demo - a multi-agent AI workflow demonstration showcasing Azure AI Foundry capabilities in a banking/treasury operations scenario.

---

## Proposed README Structure

### 1. Title & Tagline
```
# Treasury Shock Day Demo
**Multi-Agent AI Workflow for Intraday Liquidity & FX Stress Response**
```

---

### 2. Demo Scenario (The "What")

**Section: Scenario Overview**

A macro economic shock event triggers an intraday liquidity crisis combined with FX (foreign exchange) stress. This simulates a realistic "shock day" scenario that treasury operations teams face - where rapid decision-making is required across multiple data sources, forecasting models, and approval workflows.

**The Story Flow:**
1. **Trigger Event**: A macro shock is detected (e.g., sudden interest rate announcement, geopolitical event, market flash crash)
2. **Impact Assessment**: Agents assess liquidity positions, FX exposures, and policy compliance
3. **Forecast & Recommendation**: ML models predict cash flow impacts; agents recommend actions
4. **Approval Workflow**: Multi-agent system generates approval pack, routes for authorization
5. **Audit & Compliance**: Complete audit bundle generated with full traceability
6. **Finale**: Successful resolution with "confetti moment" celebration

---

### 3. Target Outcome (The "Why")

**Section: What This Demo Demonstrates**

| Capability | Before (Baseline) | After (With Foundry) |
|------------|-------------------|----------------------|
| Knowledge Retrieval | Single RAG index (WEO RAPTOR) | Foundry IQ: Multi-source KB (WEO + Policies + Fabric + Web) |
| Tool Integration | Manual API calls | Unified MCP Tools Catalog |
| Agent Orchestration | Single agent | Multi-agent workflows with state management |
| Governance | Manual tracking | Foundry Control Plane + AI Gateway |
| Identity | No agent identity | Entra Agent ID with verifiable credentials |
| Model Selection | Fixed model | Model Router (best model per task) |

---

### 4. Architecture Overview

**Section: High-Level Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FOUNDRY CONTROL PLANE                              │
│  (Fleet Visibility | Tracing | Monitoring | Evals | Red Teaming | Controls) │
├─────────────────────────────────────────────────────────────────────────────┤
│                              AI GATEWAY                                      │
│        (Cost/Usage Limits | Model Routing | Policy Enforcement)             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    FOUNDRY AGENT SERVICE                              │  │
│  │                   (Hosted Multi-Agent Workflow)                       │  │
│  │                                                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │  │
│  │  │  Liquidity  │  │     FX      │  │  Forecast   │  │  Approval   │ │  │
│  │  │   Agent     │  │   Agent     │  │   Agent     │  │   Agent     │ │  │
│  │  │             │  │             │  │             │  │             │ │  │
│  │  │ Entra ID    │  │ Entra ID    │  │ Entra ID    │  │ Entra ID    │ │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │  │
│  │         │                │                │                │        │  │
│  └─────────┼────────────────┼────────────────┼────────────────┼────────┘  │
│            │                │                │                │           │
├────────────┼────────────────┼────────────────┼────────────────┼───────────┤
│            │         KNOWLEDGE LAYER         │                │           │
│            │    ┌────────────────────────┐   │                │           │
│            │    │     FOUNDRY IQ KB      │   │                │           │
│            │    │  ┌──────┐ ┌──────────┐ │   │                │           │
│            │    │  │ WEO  │ │ Treasury │ │   │                │           │
│            │    │  │Index │ │ Policies │ │   │                │           │
│            │    │  └──────┘ └──────────┘ │   │                │           │
│            │    │  ┌──────┐ ┌──────────┐ │   │                │           │
│            │    │  │Fabric│ │   Web    │ │   │                │           │
│            │    │  │  IQ  │ │ Sources  │ │   │                │           │
│            │    │  └──────┘ └──────────┘ │   │                │           │
│            │    └────────────────────────┘   │                │           │
├────────────┼─────────────────────────────────┼────────────────┼───────────┤
│            │           MCP TOOLS CATALOG     │                │           │
│  ┌─────────┴─────────┐ ┌─────────────────────┴────┐ ┌────────┴────────┐  │
│  │   SaaS Tools      │ │    Logic Apps Connectors │ │  ML Models      │  │
│  │   (Morningstar)   │ │    (1,400+ systems)      │ │  (Nixtla/APIM)  │  │
│  └───────────────────┘ └──────────────────────────┘ └─────────────────┘  │
├─────────────────────────────────────────────────────────────────────────────┤
│                            DATA LAYER (FABRIC)                               │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐ │
│  │     Lakehouse       │  │   Semantic Model    │  │   Anomaly Detection │ │
│  │  (Treasury Data)    │  │  (Entities/Rel.)    │  │   (Fabric Agent)    │ │
│  └─────────────────────┘  └─────────────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 5. Components Checklist

**Section: What You Need to Build**

#### A) Foundry Runtime & Governance

| Component | Description | Status |
|-----------|-------------|--------|
| **Foundry Agent Service** | Hosted agents environment (preview) - no infra/container management | ⬜ To Configure |
| **Multi-Agent Workflows** | Visual designer or code-first API; long-running, stateful, recovery/debugging | ⬜ To Build |
| **Agent Memory** | (Optional) Persistent preferences/history across sessions | ⬜ Optional |
| **Foundry Control Plane** | Fleet visibility, tracing, monitoring, evals, red teaming, agent controls | ⬜ To Configure |
| **AI Gateway** | Cost/usage limits for models, agents, MCP tools | ⬜ To Configure |
| **Defender + Purview** | Security and compliance integrations (narrate if not fully configured) | ⬜ Narrate |
| **Entra Agent ID** | Identity blueprint, registry, lifecycle governance, conditional access | ⬜ To Configure |

#### B) Knowledge Layer

| Component | Description | Status |
|-----------|-------------|--------|
| **Baseline RAG** | WEO RAPTOR index in Azure AI Search (single source) | ✅ Exists |
| **Foundry IQ Knowledge Base** | Multi-source KB combining: | ⬜ To Build |
| | - WEO index (AI Search) | |
| | - Treasury Policy Pack (SharePoint/files) | |
| | - Fabric IQ semantic model (federated) | |
| | - Web sources (optional) | |

**Demo Goal**: Show before/after answer quality improvement when enabling Foundry IQ

#### C) Data Layer (Microsoft Fabric)

| Component | Description | Status |
|-----------|-------------|--------|
| **Lakehouse/Warehouse** | Synthetic treasury datasets | ⬜ To Create |
| **Semantic Model** | Entities + relationships for treasury operations | ⬜ To Build |
| **Fabric Data Agent** | Anomaly detection capabilities | ⬜ To Integrate |

#### D) Tools Layer (MCP - Model Context Protocol)

| Tool Type | Implementation | Status |
|-----------|----------------|--------|
| **SaaS Connector** | Morningstar market data provider (or alternative) | ⬜ To Configure |
| **Logic Apps Connector** | Expose Logic Apps flow as MCP tool (1,400+ systems access) | ⬜ To Build |
| **ML Model** | Nixtla time series prediction via API Management | ⬜ To Expose |

---

### 6. Agent Definitions

**Section: The Agent Cast**

#### Primary Agents

| Agent | Role | Tools Used | Knowledge Sources |
|-------|------|------------|-------------------|
| **Liquidity Assessment Agent** | Analyzes current liquidity positions, identifies stress points | Fabric Data Agent, Treasury DB queries | Foundry IQ (policies + data) |
| **FX Exposure Agent** | Evaluates foreign exchange exposures and hedging positions | Market Data (Morningstar), FX calculators | Foundry IQ (FX policies) |
| **Forecast Agent** | Predicts cash flow impacts using ML models | Nixtla time series model | Historical data, WEO reports |
| **Anomaly Detection Agent** | Identifies unusual patterns in treasury data | Fabric Anomaly Detection | Real-time transaction data |
| **Policy Compliance Agent** | Checks all recommendations against treasury policies | Policy document search | Treasury Policy Pack |
| **Approval Workflow Agent** | Orchestrates approval routing and audit trail | Logic Apps connectors, Email/Teams | Approval matrices |

#### Orchestrator Agent
- **Treasury Shock Coordinator**: Master agent that orchestrates the workflow, delegates to specialized agents, and aggregates results into final approval pack

---

### 7. Demo Flow (Step-by-Step)

**Section: Running the Demo**

```
PHASE 1: BASELINE DEMONSTRATION
├── Step 1.1: Show existing WEO RAPTOR RAG index
├── Step 1.2: Query single-source RAG with treasury question
├── Step 1.3: Highlight limitations (single source, no policy context)
│
PHASE 2: FOUNDRY IQ UPGRADE
├── Step 2.1: Connect additional sources to Foundry IQ
├── Step 2.2: Same query now returns enriched, multi-source answer
├── Step 2.3: Demonstrate agentic retrieval capabilities
│
PHASE 3: TOOL INTEGRATION
├── Step 3.1: Add Morningstar SaaS tool via MCP
├── Step 3.2: Add Logic Apps connector as MCP tool
├── Step 3.3: Expose Nixtla forecast model via API Management
├── Step 3.4: Show unified MCP tools catalog
│
PHASE 4: MULTI-AGENT WORKFLOW
├── Step 4.1: Trigger macro shock event
├── Step 4.2: Liquidity Agent assesses positions
├── Step 4.3: FX Agent evaluates exposures
├── Step 4.4: Forecast Agent predicts impacts
├── Step 4.5: Anomaly Agent flags unusual patterns
├── Step 4.6: Policy Agent validates recommendations
│
PHASE 5: GOVERNANCE & IDENTITY
├── Step 5.1: Show Foundry Control Plane dashboard
├── Step 5.2: Demonstrate AI Gateway cost/usage tracking
├── Step 5.3: Show Entra Agent ID credentials
├── Step 5.4: (Optional) Model Router selection
│
PHASE 6: FINALE
├── Step 6.1: Approval Agent generates approval pack
├── Step 6.2: Route through approval workflow
├── Step 6.3: Generate audit bundle
├── Step 6.4: 🎉 CONFETTI MOMENT - Success celebration
└── END
```

---

### 8. Prerequisites

**Section: Before You Begin**

#### Azure Services Required
- [ ] Azure subscription with appropriate permissions
- [ ] Azure AI Foundry access (preview features enabled)
- [ ] Azure AI Search instance
- [ ] Microsoft Fabric workspace
- [ ] Azure API Management instance
- [ ] Azure Logic Apps
- [ ] Microsoft Entra ID (for Agent ID)

#### Data & Models
- [ ] WEO RAPTOR index (existing)
- [ ] Synthetic treasury dataset
- [ ] Treasury policy documents
- [ ] Nixtla time series model

#### External Services
- [ ] Morningstar API access (or alternative market data provider)

---

### 9. Key Features Demonstrated

**Section: Azure AI Foundry Capabilities Showcased**

| Feature | Description | Wow Factor |
|---------|-------------|------------|
| **Foundry Agent Service** | Hosted, managed agent runtime with no infrastructure management | ⭐⭐⭐ |
| **Multi-Agent Workflows** | Visual + code-first orchestration with state management | ⭐⭐⭐⭐ |
| **Foundry IQ** | Unified knowledge base across heterogeneous sources | ⭐⭐⭐⭐⭐ |
| **MCP Tools Catalog** | Standardized tool integration (SaaS, Logic Apps, ML) | ⭐⭐⭐⭐ |
| **Foundry Control Plane** | Enterprise governance, monitoring, and controls | ⭐⭐⭐⭐ |
| **AI Gateway** | Cost/usage management across all AI operations | ⭐⭐⭐ |
| **Entra Agent ID** | Verifiable agent identity with lifecycle governance | ⭐⭐⭐⭐ |
| **Model Router** | Intelligent model selection per task | ⭐⭐⭐⭐⭐ |

---

### 10. Repository Structure (Proposed)

**Section: Project Layout**

```
treasury-shock-day-demo/
├── README.md                    # This documentation
├── PLAN.md                      # Development plan (this file)
├── docs/
│   ├── architecture.md          # Detailed architecture docs
│   ├── setup-guide.md           # Step-by-step setup instructions
│   └── demo-script.md           # Presenter script/talking points
├── agents/
│   ├── liquidity-agent/         # Liquidity Assessment Agent
│   ├── fx-agent/                # FX Exposure Agent
│   ├── forecast-agent/          # Forecast Agent
│   ├── anomaly-agent/           # Anomaly Detection Agent
│   ├── policy-agent/            # Policy Compliance Agent
│   ├── approval-agent/          # Approval Workflow Agent
│   └── coordinator-agent/       # Master Orchestrator
├── knowledge/
│   ├── weo-index/               # WEO RAPTOR index config
│   ├── policies/                # Treasury policy documents
│   └── foundry-iq-config/       # Foundry IQ KB configuration
├── data/
│   ├── synthetic-treasury/      # Synthetic treasury datasets
│   └── fabric-semantic-model/   # Fabric semantic model definitions
├── tools/
│   ├── mcp-morningstar/         # Morningstar MCP tool config
│   ├── mcp-logicapps/           # Logic Apps MCP connector
│   └── mcp-nixtla/              # Nixtla model MCP wrapper
├── workflows/
│   └── shock-day-workflow/      # Multi-agent workflow definition
├── infrastructure/
│   ├── bicep/                   # Azure Bicep templates
│   └── terraform/               # Alternative Terraform configs
└── scripts/
    ├── setup.sh                 # Environment setup script
    └── demo-reset.sh            # Reset demo to initial state
```

---

### 11. Narrative Arc (Presenter Notes)

**Section: The Story We Tell**

**Opening Hook** (30 seconds)
> "It's 9:47 AM. The Federal Reserve just announced an emergency rate hike. Your treasury team has 2 hours to assess $4.2 billion in liquidity exposure across 12 currencies. In the old world, this meant 47 phone calls, 12 spreadsheets, and hoping nothing fell through the cracks. Today, we're going to show you what happens when AI agents work together to handle this crisis."

**The Journey**
1. **The Problem**: Show the complexity of manual treasury crisis response
2. **Baseline**: Demonstrate current RAG capabilities (helpful but limited)
3. **The Upgrade**: Introduce Foundry IQ - suddenly we have context, policies, and real-time data
4. **The Tools**: Add market data, forecasting, and automation capabilities
5. **The Agents**: Watch specialized agents collaborate in real-time
6. **The Governance**: Show enterprise controls, identity, and audit trails
7. **The Resolution**: Approval pack generated, routed, approved, audited

**Closing** (30 seconds)
> "What used to take hours of frantic coordination now happens in minutes, with complete auditability, policy compliance, and AI governance. This is the future of intelligent treasury operations."

---

### 12. Success Metrics

**Section: How We Know the Demo Worked**

| Metric | Target |
|--------|--------|
| Audience engagement | Visible "wow" reactions at Foundry IQ comparison |
| Technical credibility | All components function without errors |
| Feature coverage | All 8 key capabilities demonstrated |
| Time management | Complete demo within allocated time |
| Confetti moment | Clear, satisfying conclusion |

---

## Next Steps

1. [ ] Review and approve this plan
2. [ ] Update README.md with approved content
3. [ ] Create supporting documentation files
4. [ ] Set up repository structure
5. [ ] Begin component implementation

---

*Plan created: January 2026*
*Demo Target: Azure AI Foundry Treasury Shock Day Demonstration*
