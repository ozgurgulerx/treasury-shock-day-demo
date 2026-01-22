# Azure AI Foundry: Multi-Agent Workflow Guide

This guide explains how to create sequential (chained) agent workflows in Azure AI Foundry, where one agent's output becomes the next agent's input.

---

## Table of Contents

1. [Workflow Architecture Overview](#workflow-architecture-overview)
2. [Creating Agents in AI Foundry](#creating-agents-in-ai-foundry)
3. [Workflow Patterns](#workflow-patterns)
4. [Sequential Workflow Implementation](#sequential-workflow-implementation)
5. [Agent Handoff Mechanism](#agent-handoff-mechanism)
6. [Expected Outputs](#expected-outputs)
7. [Error Handling and Recovery](#error-handling-and-recovery)

---

## Workflow Architecture Overview

### Treasury Shock Day Workflow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PAYMENT REQUEST (INPUT)                               │
│  { payment_id, beneficiary_name, amount, currency, entity, account_id }     │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AGENT 1: SANCTIONS SCREENING                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Tool: screen_sanctions (Logic Apps → AI Gateway → MCP)              │   │
│  │  Input: beneficiary_name                                             │   │
│  │  Output: { decision: BLOCK|ESCALATE|CLEAR, confidence, match_details }│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Decision Gate:                                                              │
│  ├── BLOCK → TERMINATE workflow, return REJECT                              │
│  ├── ESCALATE → TERMINATE workflow, return HOLD + compliance review         │
│  └── CLEAR → CONTINUE to Agent 2                                            │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │ (only if CLEAR)
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AGENT 2: LIQUIDITY SCREENING                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Tool: compute_liquidity_impact (Azure Function → AI Gateway → MCP)  │   │
│  │  Input: payment_id OR { amount, currency, account_id, entity }       │   │
│  │  Output: { breach, gap, headroom, recommendation }                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Output includes:                                                            │
│  ├── breach_assessment: { breach: true|false, gap, headroom }               │
│  ├── account_summary: { balances, flows }                                   │
│  └── recommendation: { action: RELEASE|HOLD, alternatives }                 │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                  AGENT 3: OPERATIONAL PROCEDURES                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Tool: search_treasury_kb (Azure AI Search → AI Gateway → MCP)       │   │
│  │  Input: sanctions_result + liquidity_result                          │   │
│  │  Output: { final_action, required_approvals, workflow_steps, audit } │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Applies:                                                                    │
│  ├── Decision matrix from runbooks                                          │
│  ├── Approval matrix based on amount/type                                   │
│  └── Audit bundle requirements                                              │
└─────────────────────────────────┬───────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FINAL OUTPUT                                          │
│  {                                                                           │
│    final_decision: PROCEED|HOLD|REJECT,                                     │
│    required_approvers: [...],                                                │
│    workflow_steps: [...],                                                    │
│    audit_bundle: {...},                                                      │
│    agent_trace: [agent1_output, agent2_output, agent3_output]               │
│  }                                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Creating Agents in AI Foundry

### Method 1: Azure AI Foundry Portal (Visual Designer)

1. **Navigate to AI Foundry Studio**
   ```
   https://ai.azure.com → Your Project → Agents
   ```

2. **Create New Agent**
   - Click "Create Agent"
   - Select "Custom Agent" template
   - Configure:
     - Name: `sanctions-screening-agent`
     - Description: "Screens beneficiaries against OFAC SDN list"
     - System Prompt: (paste from agent_configurations.md)

3. **Add MCP Tools**
   - Go to "Tools" tab
   - Click "Add Tool" → "MCP Tool"
   - Configure connection to AI Gateway endpoint
   - Select tool: `screen_sanctions`

4. **Configure Model**
   - Go to "Model" tab
   - Select deployment (e.g., `gpt-4o` or use Model Router)
   - Set temperature, max tokens

5. **Repeat for all three agents**

### Method 2: Code-First (Python SDK)

```python
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Initialize client
project_client = AIProjectClient(
    credential=DefaultAzureCredential(),
    subscription_id="<subscription-id>",
    resource_group_name="<resource-group>",
    project_name="<project-name>"
)

# Create Sanctions Screening Agent
sanctions_agent = project_client.agents.create(
    name="sanctions-screening-agent",
    description="Screens beneficiaries against OFAC SDN list",
    instructions="""
    You are the Sanctions Screening Agent for treasury operations.
    [... full system prompt from agent_configurations.md ...]
    """,
    model="gpt-4o",
    tools=[
        {
            "type": "mcp",
            "name": "screen_sanctions",
            "endpoint": "https://ai-gateway.azure.com/mcp/sanctions-screening"
        }
    ]
)

# Create Liquidity Screening Agent
liquidity_agent = project_client.agents.create(
    name="liquidity-screening-agent",
    description="Computes intraday liquidity impact",
    instructions="""
    You are the Liquidity Screening Agent for treasury operations.
    [... full system prompt from agent_configurations.md ...]
    """,
    model="gpt-4o",
    tools=[
        {
            "type": "mcp",
            "name": "compute_liquidity_impact",
            "endpoint": "https://ai-gateway.azure.com/mcp/liquidity-gate"
        }
    ]
)

# Create Operational Procedures Agent
ops_agent = project_client.agents.create(
    name="operational-procedures-agent",
    description="Applies policies and determines workflow",
    instructions="""
    You are the Operational Procedures Agent for treasury operations.
    [... full system prompt from agent_configurations.md ...]
    """,
    model="gpt-4o",
    tools=[
        {
            "type": "mcp",
            "name": "search_treasury_kb",
            "endpoint": "https://ai-gateway.azure.com/mcp/treasury-kb"
        }
    ]
)
```

---

## Workflow Patterns

### Pattern 1: Sequential (Chain) - Our Use Case

```
Agent 1 → Agent 2 → Agent 3
```

- Each agent completes before the next starts
- Output of Agent N becomes input context for Agent N+1
- Early termination possible (e.g., BLOCK at sanctions)

### Pattern 2: Parallel (Fan-out/Fan-in)

```
         ┌→ Agent A ─┐
Input →  ├→ Agent B ─┼→ Aggregator → Output
         └→ Agent C ─┘
```

- All agents run simultaneously
- Results aggregated at the end
- Use for independent assessments

### Pattern 3: Conditional (Router)

```
              ┌→ Path A → Agent X
Input → Router├→ Path B → Agent Y
              └→ Path C → Agent Z
```

- Router decides which path based on input
- Different agents for different scenarios

### Pattern 4: Iterative (Loop)

```
Input → Agent → Evaluator → [Continue?] → Agent → ...
                    └→ Output
```

- Agent refines output iteratively
- Evaluator decides when to stop

---

## Sequential Workflow Implementation

### AI Foundry Workflow Definition (YAML)

```yaml
# workflow_treasury_shock.yaml
name: treasury-shock-day-workflow
description: Multi-agent workflow for emergency payment processing
version: "1.0"

# Workflow-level configuration
config:
  max_turns: 20
  timeout_seconds: 300
  trace_enabled: true
  memory_enabled: true

# Agent definitions (reference existing agents)
agents:
  - id: sanctions_screener
    agent_ref: sanctions-screening-agent

  - id: liquidity_screener
    agent_ref: liquidity-screening-agent

  - id: ops_procedures
    agent_ref: operational-procedures-agent

# Workflow steps
steps:
  - id: step_1_sanctions
    agent: sanctions_screener
    input:
      source: workflow_input
      mapping:
        name: "$.payment_request.beneficiary_name"
        context:
          payment_id: "$.payment_request.payment_id"
          amount: "$.payment_request.amount"
          currency: "$.payment_request.currency"
    output_key: sanctions_result

    # Conditional routing
    routing:
      - condition: "$.sanctions_result.decision == 'BLOCK'"
        goto: terminate_block
      - condition: "$.sanctions_result.decision == 'ESCALATE'"
        goto: terminate_escalate
      - condition: "$.sanctions_result.decision == 'CLEAR'"
        goto: step_2_liquidity

  - id: step_2_liquidity
    agent: liquidity_screener
    input:
      source: workflow_input
      additional_context:
        sanctions_result: "$.sanctions_result"
      mapping:
        payment_id: "$.payment_request.payment_id"
        amount: "$.payment_request.amount"
        currency: "$.payment_request.currency"
        account_id: "$.payment_request.account_id"
        entity: "$.payment_request.entity"
        beneficiary_name: "$.payment_request.beneficiary_name"
    output_key: liquidity_result
    routing:
      - goto: step_3_operations

  - id: step_3_operations
    agent: ops_procedures
    input:
      source: accumulated
      mapping:
        sanctions_decision: "$.sanctions_result.decision"
        liquidity_breach: "$.liquidity_result.breach_assessment.breach"
        before_cutoff: true  # computed from current time vs cutoff
        amount_usd: "$.payment_request.amount"
        payment_type: "$.payment_request.payment_type"
    output_key: ops_result
    routing:
      - goto: finalize

  # Termination nodes
  - id: terminate_block
    type: terminate
    output:
      final_decision: "REJECT"
      reason: "Sanctions BLOCK - payment rejected"
      agent_results:
        sanctions: "$.sanctions_result"

  - id: terminate_escalate
    type: terminate
    output:
      final_decision: "HOLD"
      reason: "Sanctions ESCALATE - pending compliance review"
      agent_results:
        sanctions: "$.sanctions_result"

  - id: finalize
    type: aggregate
    output:
      final_decision: "$.ops_result.workflow_determination.final_action"
      reason: "$.ops_result.workflow_determination.reason"
      required_approvers: "$.ops_result.required_approvals"
      workflow_steps: "$.ops_result.workflow_steps"
      audit_bundle: "$.ops_result.audit_bundle"
      agent_results:
        sanctions: "$.sanctions_result"
        liquidity: "$.liquidity_result"
        operations: "$.ops_result"
```

### Python Orchestration Code

```python
"""
treasury_workflow.py
Sequential multi-agent workflow for Treasury Shock Day
"""

import json
import uuid
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, asdict

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentThread, ThreadMessage
from azure.identity import DefaultAzureCredential


@dataclass
class PaymentRequest:
    payment_id: str
    beneficiary_name: str
    amount: float
    currency: str
    account_id: str
    entity: str
    payment_type: str
    timestamp_utc: str
    originator: str


@dataclass
class WorkflowContext:
    workflow_run_id: str
    payment_request: PaymentRequest
    sanctions_result: Optional[dict] = None
    liquidity_result: Optional[dict] = None
    ops_result: Optional[dict] = None
    final_decision: Optional[str] = None
    termination_reason: Optional[str] = None


class TreasuryWorkflow:
    """Orchestrates the sequential agent workflow."""

    def __init__(self, project_client: AIProjectClient):
        self.client = project_client
        self.agents = {
            "sanctions": self._get_agent("sanctions-screening-agent"),
            "liquidity": self._get_agent("liquidity-screening-agent"),
            "operations": self._get_agent("operational-procedures-agent"),
        }

    def _get_agent(self, name: str):
        """Retrieve agent by name."""
        agents = self.client.agents.list()
        for agent in agents:
            if agent.name == name:
                return agent
        raise ValueError(f"Agent not found: {name}")

    def run(self, payment_request: PaymentRequest) -> dict:
        """Execute the full workflow."""

        # Initialize workflow context
        context = WorkflowContext(
            workflow_run_id=f"WF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}",
            payment_request=payment_request
        )

        print(f"Starting workflow: {context.workflow_run_id}")

        # Step 1: Sanctions Screening
        print("\n=== Step 1: Sanctions Screening ===")
        context.sanctions_result = self._run_sanctions_agent(context)

        # Check for early termination
        decision = context.sanctions_result.get("decision", "CLEAR")
        if decision == "BLOCK":
            context.final_decision = "REJECT"
            context.termination_reason = "Sanctions BLOCK"
            return self._build_final_output(context)
        elif decision == "ESCALATE":
            context.final_decision = "HOLD"
            context.termination_reason = "Sanctions ESCALATE - compliance review required"
            return self._build_final_output(context)

        # Step 2: Liquidity Screening (only if sanctions CLEAR)
        print("\n=== Step 2: Liquidity Screening ===")
        context.liquidity_result = self._run_liquidity_agent(context)

        # Step 3: Operational Procedures
        print("\n=== Step 3: Operational Procedures ===")
        context.ops_result = self._run_operations_agent(context)

        # Build final output
        context.final_decision = context.ops_result.get("workflow_determination", {}).get("final_action", "HOLD")
        return self._build_final_output(context)

    def _run_sanctions_agent(self, context: WorkflowContext) -> dict:
        """Run sanctions screening agent."""
        thread = self.client.agents.create_thread()

        # Create message with payment context
        message_content = f"""
        Screen the following beneficiary for sanctions:

        Beneficiary Name: {context.payment_request.beneficiary_name}
        Payment Context:
        - Payment ID: {context.payment_request.payment_id}
        - Amount: {context.payment_request.amount} {context.payment_request.currency}

        Call the screen_sanctions tool and return your assessment.
        """

        self.client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=message_content
        )

        # Run the agent
        run = self.client.agents.create_run(
            thread_id=thread.id,
            assistant_id=self.agents["sanctions"].id
        )

        # Wait for completion and get result
        run = self._wait_for_run(thread.id, run.id)
        messages = self.client.agents.list_messages(thread_id=thread.id)

        # Parse agent response (last assistant message)
        return self._parse_agent_response(messages)

    def _run_liquidity_agent(self, context: WorkflowContext) -> dict:
        """Run liquidity screening agent."""
        thread = self.client.agents.create_thread()

        message_content = f"""
        Compute liquidity impact for the following payment:

        Payment ID: {context.payment_request.payment_id}
        Amount: {context.payment_request.amount}
        Currency: {context.payment_request.currency}
        Account ID: {context.payment_request.account_id}
        Entity: {context.payment_request.entity}
        Beneficiary: {context.payment_request.beneficiary_name}
        Timestamp: {context.payment_request.timestamp_utc}

        Previous Agent Result (Sanctions): {json.dumps(context.sanctions_result, indent=2)}

        Call the compute_liquidity_impact tool and return your assessment.
        """

        self.client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=message_content
        )

        run = self.client.agents.create_run(
            thread_id=thread.id,
            assistant_id=self.agents["liquidity"].id
        )

        run = self._wait_for_run(thread.id, run.id)
        messages = self.client.agents.list_messages(thread_id=thread.id)

        return self._parse_agent_response(messages)

    def _run_operations_agent(self, context: WorkflowContext) -> dict:
        """Run operational procedures agent."""
        thread = self.client.agents.create_thread()

        # Determine if before cutoff (simplified - would check actual cutoff time)
        before_cutoff = True

        message_content = f"""
        Determine the correct workflow for this payment based on previous agent results:

        Payment Summary:
        - Payment ID: {context.payment_request.payment_id}
        - Amount: {context.payment_request.amount} {context.payment_request.currency}
        - Payment Type: {context.payment_request.payment_type}
        - Entity: {context.payment_request.entity}

        Sanctions Screening Result:
        {json.dumps(context.sanctions_result, indent=2)}

        Liquidity Screening Result:
        {json.dumps(context.liquidity_result, indent=2)}

        Context:
        - Before Cutoff: {before_cutoff}

        Query the treasury knowledge base and determine:
        1. The correct workflow action (PROCEED/HOLD/REJECT)
        2. Required approvers
        3. Workflow steps
        4. Audit bundle requirements
        """

        self.client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content=message_content
        )

        run = self.client.agents.create_run(
            thread_id=thread.id,
            assistant_id=self.agents["operations"].id
        )

        run = self._wait_for_run(thread.id, run.id)
        messages = self.client.agents.list_messages(thread_id=thread.id)

        return self._parse_agent_response(messages)

    def _wait_for_run(self, thread_id: str, run_id: str, timeout: int = 120):
        """Wait for agent run to complete."""
        import time
        start = time.time()
        while time.time() - start < timeout:
            run = self.client.agents.get_run(thread_id=thread_id, run_id=run_id)
            if run.status in ["completed", "failed", "cancelled"]:
                return run
            time.sleep(1)
        raise TimeoutError("Agent run timed out")

    def _parse_agent_response(self, messages) -> dict:
        """Parse JSON from agent's last message."""
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                content = msg.content[0].text.value
                # Try to extract JSON from response
                try:
                    # Handle markdown code blocks
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0]
                        return json.loads(json_str)
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0]
                        return json.loads(json_str)
                    else:
                        return json.loads(content)
                except json.JSONDecodeError:
                    return {"raw_response": content}
        return {}

    def _build_final_output(self, context: WorkflowContext) -> dict:
        """Build the final workflow output."""
        return {
            "workflow_run_id": context.workflow_run_id,
            "final_decision": {
                "action": context.final_decision,
                "reason": context.termination_reason or context.ops_result.get("workflow_determination", {}).get("reason", ""),
                "executed_at": datetime.utcnow().isoformat() + "Z"
            },
            "agent_results": {
                "sanctions_screening": context.sanctions_result,
                "liquidity_screening": context.liquidity_result,
                "operational_procedures": context.ops_result
            },
            "approval_status": {
                "required_approvers": context.ops_result.get("required_approvals", []) if context.ops_result else [],
                "obtained_approvals": [],
                "pending_approvals": context.ops_result.get("required_approvals", []) if context.ops_result else []
            },
            "audit_bundle": context.ops_result.get("audit_bundle", {}) if context.ops_result else {},
            "workflow_trace": {
                "steps_completed": [
                    "sanctions_screening",
                    "liquidity_screening" if context.liquidity_result else None,
                    "operational_procedures" if context.ops_result else None
                ],
                "early_termination": context.termination_reason is not None
            }
        }


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = AIProjectClient(
        credential=DefaultAzureCredential(),
        subscription_id="your-subscription-id",
        resource_group_name="your-resource-group",
        project_name="your-project"
    )

    # Create workflow
    workflow = TreasuryWorkflow(client)

    # Sample payment request
    payment = PaymentRequest(
        payment_id="TXN-EMRG-001",
        beneficiary_name="ACME Trading LLC",
        amount=250000,
        currency="USD",
        account_id="ACC-BAN-001",
        entity="BankSubsidiary_TR",
        payment_type="EMERGENCY",
        timestamp_utc="2026-01-22 10:25:00",
        originator="treasury-ops@bank.local"
    )

    # Run workflow
    result = workflow.run(payment)
    print(json.dumps(result, indent=2))
```

---

## Agent Handoff Mechanism

### Context Accumulation Pattern

Each agent receives the accumulated context from previous agents:

```python
# Context passed between agents
accumulated_context = {
    "workflow_run_id": "WF-2026-01-22-001",
    "payment_request": {
        # Original payment details
    },
    "agent_results": {
        "sanctions_screening": {
            # Agent 1 output (available for Agent 2+)
        },
        "liquidity_screening": {
            # Agent 2 output (available for Agent 3+)
        }
    },
    "workflow_state": {
        "current_step": 3,
        "steps_completed": ["sanctions", "liquidity"],
        "can_proceed": True
    }
}
```

### Message Format for Handoff

```python
# Template for passing context to next agent
handoff_message = f"""
WORKFLOW CONTEXT
================
Workflow ID: {context.workflow_run_id}
Current Step: {step_number} of 3

PREVIOUS AGENT RESULTS
======================
{json.dumps(context.agent_results, indent=2)}

YOUR TASK
=========
{agent_specific_instructions}

Respond with your assessment in the required JSON format.
"""
```

---

## Expected Outputs

### Scenario 1: Sanctions BLOCK (Early Termination)

**Input:**
```json
{
  "payment_id": "TXN-001",
  "beneficiary_name": "BANK MASKAN",
  "amount": 100000,
  "currency": "USD"
}
```

**Output:**
```json
{
  "workflow_run_id": "WF-20260122103000-a1b2c3",
  "final_decision": {
    "action": "REJECT",
    "reason": "Sanctions BLOCK - direct match to OFAC SDN entity",
    "executed_at": "2026-01-22T10:30:15Z"
  },
  "agent_results": {
    "sanctions_screening": {
      "decision": "BLOCK",
      "confidence": 98,
      "match_type": "EXACT",
      "matched_entity": "BANK MASKAN"
    },
    "liquidity_screening": null,
    "operational_procedures": null
  },
  "workflow_trace": {
    "steps_completed": ["sanctions_screening"],
    "early_termination": true
  }
}
```

### Scenario 2: CLEAR + No Breach (Full Flow - PROCEED)

**Input:**
```json
{
  "payment_id": "TXN-002",
  "beneficiary_name": "ACME Corp",
  "amount": 50000,
  "currency": "USD"
}
```

**Output:**
```json
{
  "workflow_run_id": "WF-20260122103500-d4e5f6",
  "final_decision": {
    "action": "PROCEED",
    "reason": "Sanctions CLEAR, no liquidity breach, before cutoff",
    "executed_at": "2026-01-22T10:35:45Z"
  },
  "agent_results": {
    "sanctions_screening": {
      "decision": "CLEAR",
      "confidence": 0,
      "match_type": "NONE"
    },
    "liquidity_screening": {
      "breach": false,
      "headroom": 1500000,
      "recommendation": "RELEASE"
    },
    "operational_procedures": {
      "final_action": "PROCEED",
      "required_approvals": [{"role": "Payments Operator"}]
    }
  },
  "approval_status": {
    "required_approvers": ["Payments Operator"],
    "pending_approvals": ["Payments Operator"]
  }
}
```

### Scenario 3: CLEAR + Breach (Full Flow - HOLD)

**Input:**
```json
{
  "payment_id": "TXN-003",
  "beneficiary_name": "Large Vendor Inc",
  "amount": 2500000,
  "currency": "USD"
}
```

**Output:**
```json
{
  "workflow_run_id": "WF-20260122104000-g7h8i9",
  "final_decision": {
    "action": "HOLD",
    "reason": "Sanctions CLEAR but payment would breach buffer by $500,000",
    "executed_at": "2026-01-22T10:40:30Z"
  },
  "agent_results": {
    "sanctions_screening": {
      "decision": "CLEAR",
      "confidence": 0
    },
    "liquidity_screening": {
      "breach": true,
      "gap": 500000,
      "recommendation": "HOLD",
      "alternatives": ["Delay", "Partial release", "Escalate for funding"]
    },
    "operational_procedures": {
      "final_action": "HOLD",
      "required_approvals": [
        {"role": "Treasury Manager", "authority": "Evaluate options"},
        {"role": "Head of Treasury", "authority": "Override approval"}
      ],
      "workflow_steps": [
        {"step": 1, "action": "HOLD payment"},
        {"step": 2, "action": "Notify Treasury Manager"},
        {"step": 3, "action": "Evaluate options"}
      ]
    }
  },
  "approval_status": {
    "required_approvers": ["Treasury Manager", "Head of Treasury"],
    "pending_approvals": ["Treasury Manager", "Head of Treasury"]
  }
}
```

---

## Error Handling and Recovery

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def run_agent_with_retry(self, agent_id: str, thread_id: str):
    """Run agent with automatic retry on failure."""
    run = self.client.agents.create_run(
        thread_id=thread_id,
        assistant_id=agent_id
    )
    return self._wait_for_run(thread_id, run.id)
```

### Checkpoint and Resume

```python
def save_checkpoint(context: WorkflowContext, step: str):
    """Save workflow state for recovery."""
    checkpoint = {
        "workflow_run_id": context.workflow_run_id,
        "last_completed_step": step,
        "context": asdict(context),
        "timestamp": datetime.utcnow().isoformat()
    }
    # Save to blob storage or database

def resume_from_checkpoint(workflow_run_id: str) -> WorkflowContext:
    """Resume workflow from last checkpoint."""
    # Load checkpoint from storage
    # Return hydrated WorkflowContext
```

---

*Document Version: 1.0*
*Created: 2026-01-22*
