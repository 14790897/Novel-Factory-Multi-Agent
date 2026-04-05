"""Chapter Outliner Agent — expands a chapter outline into detailed scene beats."""

import json

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.utils.json import parse_json_markdown

from novel_factory.prompts import OUTLINER_SYSTEM
from novel_factory.state import NovelState


def outliner_node(state: NovelState, llm) -> dict:
    """Generate scene beats for the current chapter."""
    chapter_idx = state["current_chapter"]
    chapter_outline = state["chapter_outlines"][chapter_idx]
    story_bible = state["story_bible"]
    past_summaries = state.get("past_summaries", [])

    summaries_text = ""
    if past_summaries:
        summaries_text = "\n\n前情摘要：\n" + "\n---\n".join(
            f"第{i+1}章：{s}" for i, s in enumerate(past_summaries)
        )

    messages = [
        SystemMessage(content=OUTLINER_SYSTEM),
        HumanMessage(content=(
            f"设定集：\n{json.dumps(story_bible, ensure_ascii=False, indent=2)}\n\n"
            f"当前章节大纲：\n{json.dumps(chapter_outline, ensure_ascii=False, indent=2)}"
            f"{summaries_text}\n\n"
            f"请为本章生成详细的场景节拍（Scene Beats），严格按 JSON 数组格式输出。"
        )),
    ]

    response = llm.invoke(messages)
    content = response.content

    beats = parse_json_markdown(content)

    return {
        "current_beats": beats,
        "current_beat_index": 0,
        "completed_scenes": [],
        "revision_count": 0,
    }
