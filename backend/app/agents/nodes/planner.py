"""
FinSight AI — Planner Agent
Understands user intent, decomposes complex queries into subtasks,
and creates an execution plan for the agent pipeline.
"""

import json
from datetime import datetime, timezone

import structlog

from app.agents.llm.provider import get_llm_provider
from app.agents.state import GraphState

logger = structlog.get_logger()

PLANNER_SYSTEM_PROMPT = """You are the Planner Agent for FinSight AI, a financial intelligence platform.

Your role is to:
1. Understand the user's financial query intent
2. Identify which companies, regulations, or topics are involved
3. Decompose the query into subtasks for specialized agents
4. Create an optimal execution plan

Available agents:
- financial_research: Retrieves financial documents, annual reports, earnings transcripts
- regulatory: Searches regulatory databases for RBI/SEBI circulars and banking regulations
- market_intel: Gathers market news, trends, and company announcements
- analysis: Calculates financial ratios (ROE, ROA, D/E, revenue growth, margins)
- verification: Validates claims, checks citation grounding, detects hallucinations
- report_generation: Generates structured financial reports with citations

Respond with a JSON object containing:
{
    "intent": "brief description of what the user wants",
    "companies": ["list of company names mentioned or implied"],
    "topics": ["list of financial topics"],
    "needs_financial_data": true/false,
    "needs_regulatory_data": true/false,
    "needs_market_data": true/false,
    "needs_analysis": true/false,
    "generate_report": true/false,
    "subtasks": [
        {
            "id": "task_1",
            "agent": "agent_name",
            "description": "what this subtask should accomplish",
            "priority": 1
        }
    ],
    "execution_order": ["agent_name_1", "agent_name_2", ...]
}"""


async def planner_node(state: GraphState) -> GraphState:
    """
    Planner Agent node — analyzes user query and creates execution plan.
    """
    query = state.get("query", "")
    companies = state.get("companies", [])

    logger.info("planner_started", query=query[:100])

    llm = get_llm_provider()

    prompt = f"""Analyze this financial query and create an execution plan.

User Query: {query}
Known Companies: {json.dumps(companies) if companies else 'None specified'}
Include Regulations: {state.get('include_regulations', True)}
Include Market Data: {state.get('include_market_data', True)}
Generate Full Report: {state.get('generate_report', False)}

Create a detailed execution plan."""

    try:
        result = await llm.generate_structured(
            prompt=prompt,
            system_prompt=PLANNER_SYSTEM_PROMPT,
        )

        plan = result["content"]
        tokens = result.get("tokens", 0)

        # Extract companies from plan if not already specified
        plan_companies = plan.get("companies", [])
        all_companies = list(set(companies + plan_companies))

        # Build subtasks
        subtasks = plan.get("subtasks", [])

        execution_step = {
            "agent_name": "planner",
            "status": "completed",
            "message": f"Analyzed query intent: {plan.get('intent', 'financial analysis')}. "
                       f"Created {len(subtasks)} subtasks for {len(all_companies)} companies.",
            "data": {"plan": plan},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        return {
            **state,
            "plan": [plan],
            "subtasks": subtasks,
            "companies": all_companies,
            "current_step": "financial_research",
            "execution_steps": state.get("execution_steps", []) + [execution_step],
            "total_tokens": state.get("total_tokens", 0) + tokens,
        }

    except Exception as e:
        logger.error("planner_failed", error=str(e))
        return {
            **state,
            "current_step": "financial_research",
            "errors": state.get("errors", []) + [f"Planner error: {str(e)}"],
            "execution_steps": state.get("execution_steps", []) + [{
                "agent_name": "planner",
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }
