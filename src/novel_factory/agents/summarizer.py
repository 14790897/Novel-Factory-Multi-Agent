"""Summarizer Agent — compresses a finished chapter into a plot summary."""

from langchain_core.messages import HumanMessage, SystemMessage

from novel_factory.prompts import SUMMARIZER_SYSTEM
from novel_factory.state import NovelState


def summarizer_node(state: NovelState, llm) -> dict:
    """Summarize the completed chapter and archive it."""
    chapter_idx = state["current_chapter"]
    chapter_outline = state["chapter_outlines"][chapter_idx]
    scenes = state["completed_scenes"]
    full_text = "\n\n".join(scenes)

    messages = [
        SystemMessage(content=SUMMARIZER_SYSTEM),
        HumanMessage(content=(
            f"## 章节标题\n{chapter_outline.get('title', f'第{chapter_idx+1}章')}\n\n"
            f"## 章节全文\n{full_text}\n\n"
            f"请为本章撰写精炼的剧情摘要。"
        )),
    ]

    response = llm.invoke(messages)
    summary = response.content.strip()

    past_summaries = list(state.get("past_summaries", []))
    past_summaries.append(summary)

    completed_chapters = list(state.get("completed_chapters", []))
    completed_chapters.append({
        "chapter_number": chapter_idx + 1,
        "title": chapter_outline.get("title", f"第{chapter_idx+1}章"),
        "text": full_text,
        "summary": summary,
    })

    return {
        "past_summaries": past_summaries,
        "completed_chapters": completed_chapters,
        "current_chapter": chapter_idx + 1,
    }
