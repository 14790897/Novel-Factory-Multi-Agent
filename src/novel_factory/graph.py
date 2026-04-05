"""LangGraph orchestration — wires all agents into the novel writing pipeline."""

from functools import partial

from langgraph.graph import END, StateGraph

from novel_factory.agents.architect import architect_node
from novel_factory.agents.editor import editor_node
from novel_factory.agents.novelist import novelist_node
from novel_factory.agents.outliner import outliner_node
from novel_factory.agents.summarizer import summarizer_node
from novel_factory.state import NovelState


# ---------------------------------------------------------------------------
# Transition helper: archive approved draft into completed_scenes and advance
# the beat index before routing.
# ---------------------------------------------------------------------------

def _advance_beat(state: NovelState) -> dict:
    """Move the approved draft into completed_scenes and bump the beat index."""
    completed = list(state.get("completed_scenes", []))
    completed.append(state["draft_text"])
    return {
        "completed_scenes": completed,
        "current_beat_index": state["current_beat_index"] + 1,
        "revision_count": 0,
        "editor_feedback": "",
    }


# ---------------------------------------------------------------------------
# Conditional edge functions
# ---------------------------------------------------------------------------

def _after_editor(state: NovelState) -> str:
    """Decide what to do after the editor reviews a draft.

    Returns one of:
      - "revise"          → send back to novelist for revision
      - "advance_beat"    → draft approved, move to the next beat
    """
    if not state["editor_approved"] and state["revision_count"] < state["max_revisions"]:
        return "revise"
    # Either approved or exhausted revision budget — accept draft
    return "advance_beat"


def _after_advance(state: NovelState) -> str:
    """Decide what to do after advancing the beat index.

    Returns one of:
      - "next_beat"       → more beats remain in this chapter
      - "summarize"       → chapter complete, summarize it
    """
    if state["current_beat_index"] < len(state["current_beats"]):
        return "next_beat"
    return "summarize"


def _after_summary(state: NovelState) -> str:
    """Decide what to do after a chapter summary.

    Returns one of:
      - "next_chapter"    → more chapters to write
      - "end"             → novel is complete
    """
    if state["current_chapter"] < len(state["chapter_outlines"]):
        return "next_chapter"
    return "end"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(llm):
    """Construct and compile the Novel Factory LangGraph.

    Args:
        llm: A LangChain chat model instance (e.g. ChatOpenAI, ChatAnthropic).

    Returns:
        A compiled LangGraph ready to be invoked.
    """
    graph = StateGraph(NovelState)

    # --- nodes (bind the shared LLM via partial) ---
    graph.add_node("architect", partial(architect_node, llm=llm))
    graph.add_node("outliner", partial(outliner_node, llm=llm))
    graph.add_node("novelist", partial(novelist_node, llm=llm))
    graph.add_node("editor", partial(editor_node, llm=llm))
    graph.add_node("advance_beat", _advance_beat)
    graph.add_node("summarizer", partial(summarizer_node, llm=llm))

    # --- edges ---
    graph.set_entry_point("architect")

    # architect → outliner (always)
    graph.add_edge("architect", "outliner")

    # outliner → novelist (always)
    graph.add_edge("outliner", "novelist")

    # novelist → editor (always)
    graph.add_edge("novelist", "editor")

    # editor → conditional: revise or advance
    graph.add_conditional_edges(
        "editor",
        _after_editor,
        {
            "revise": "novelist",
            "advance_beat": "advance_beat",
        },
    )

    # advance_beat → conditional: next beat or summarize
    graph.add_conditional_edges(
        "advance_beat",
        _after_advance,
        {
            "next_beat": "novelist",
            "summarize": "summarizer",
        },
    )

    # summarizer → conditional: next chapter or end
    graph.add_conditional_edges(
        "summarizer",
        _after_summary,
        {
            "next_chapter": "outliner",
            "end": END,
        },
    )

    return graph.compile()
