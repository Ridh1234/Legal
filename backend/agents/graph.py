from typing import Dict, Any
import logging

try:
    from langgraph.graph import StateGraph, END  # type: ignore
    _HAS_LANGGRAPH = True
except Exception:  # ImportError or runtime errors due to version mismatch
    _HAS_LANGGRAPH = False

from .analyze_node import analyze_email_node
from .draft_node import draft_reply_node

logger = logging.getLogger(__name__)


async def run_pipeline(
    *,
    email_text: str,
    contract_snippet: str | None = None,
    analysis: Dict[str, Any] | None = None,
    variant: str | None = None,
    mode: str = "process",
    debug: bool = False,
) -> Dict[str, Any]:
    """
    Run the 2-node pipeline using LangGraph.
    Modes:
      - analyze: only analyze node
      - draft: requires analysis provided, runs draft node
      - process: analyze then draft
    """
    state: Dict[str, Any] = {
        "email_text": email_text,
        "contract_snippet": contract_snippet,
        "analysis": analysis,
        "variant": variant,
        "debug": debug,
        "trace": [],
    }

    if mode not in {"analyze", "draft", "process"}:
        raise ValueError("Invalid mode")

    if mode == "analyze":
        result = await analyze_email_node(state)
        state.update(result)
        return {"analysis": state["analysis"]}

    if mode == "draft" and not analysis:
        raise ValueError("'draft' mode requires 'analysis' input")

    if _HAS_LANGGRAPH:
        # Build graph lazily to avoid global import side effects
        workflow = StateGraph(dict)
        workflow.add_node("analyze_email", analyze_email_node)
        workflow.add_node("draft_reply", draft_reply_node)

        if mode == "process":
            workflow.set_entry_point("analyze_email")
            workflow.add_edge("analyze_email", "draft_reply")
            workflow.add_edge("draft_reply", END)
        else:  # draft only
            workflow.set_entry_point("draft_reply")
            workflow.add_edge("draft_reply", END)

        graph = workflow.compile()

        async for event in graph.astream(state):
            if debug:
                for k, v in event.items():
                    if k == "__end__":
                        continue
                    # Append minimal trace info (no chain-of-thought)
                    state.setdefault("trace", []).append({"event": k})
    else:
        logger.warning("LangGraph not available; running sequentially")
        if mode == "process":
            # analyze then draft sequentially
            result = await analyze_email_node(state)
            state.update(result)
            result = await draft_reply_node(state)
            state.update(result)
        else:  # draft only
            result = await draft_reply_node(state)
            state.update(result)

    # Final state is in 'state' after running graph
    return {
        "analysis": state.get("analysis"),
        "draft": state.get("draft"),
        "risk_score": state.get("risk_score"),
        "trace": state.get("trace"),
    }
