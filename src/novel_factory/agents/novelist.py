"""Novelist Agent — writes the actual prose for a single scene beat."""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from novel_factory.prompts import NOVELIST_SYSTEM
from novel_factory.state import NovelState


def _extract_character_cards(story_bible: dict, character_names: list[str]) -> list[dict]:
    """Pull relevant character cards from the Story Bible."""
    all_chars = story_bible.get("characters", [])
    return [c for c in all_chars if c.get("name") in character_names]


def novelist_node(state: NovelState, llm) -> dict:
    """Draft prose for the current scene beat."""
    beat = state["current_beats"][state["current_beat_index"]]
    story_bible = state["story_bible"]
    past_summaries = state.get("past_summaries", [])
    editor_feedback = state.get("editor_feedback", "")

    # Only supply the last 3 chapter summaries to avoid context overload
    recent_summaries = past_summaries[-3:] if past_summaries else []

    # Extract character cards for characters in this scene
    character_cards = _extract_character_cards(
        story_bible, beat.get("characters", [])
    )

    prompt_parts = [
        f"## 当前场景节拍\n{json.dumps(beat, ensure_ascii=False, indent=2)}",
        f"\n## 出场角色卡片\n{json.dumps(character_cards, ensure_ascii=False, indent=2)}",
    ]

    if recent_summaries:
        summaries_text = "\n---\n".join(
            f"第{len(past_summaries) - len(recent_summaries) + i + 1}章：{s}"
            for i, s in enumerate(recent_summaries)
        )
        prompt_parts.append(f"\n## 近期剧情摘要\n{summaries_text}")

    if editor_feedback:
        prompt_parts.append(
            f"\n## 编辑修改意见（请在本次修改中逐一解决）\n{editor_feedback}"
        )

    messages = [
        SystemMessage(content=NOVELIST_SYSTEM),
        HumanMessage(content="\n".join(prompt_parts)),
    ]

    response = llm.invoke(messages)

    return {
        "draft_text": response.content,
    }
