"""Chief Architect Agent — generates the Story Bible and chapter outlines."""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from novel_factory.prompts import ARCHITECT_SYSTEM
from novel_factory.state import NovelState


def architect_node(state: NovelState, llm) -> dict:
    """Generate the Story Bible and chapter outlines from user input."""
    num_chapters = len(state.get("chapter_outlines", [])) or 5

    messages = [
        SystemMessage(content=ARCHITECT_SYSTEM),
        HumanMessage(content=(
            f"请根据以下创意灵感，创建一部长篇小说的完整设定集和章节大纲。\n\n"
            f"创意灵感：{state['user_input']}\n\n"
            f"要求章节数量：{num_chapters} 章\n\n"
            f"请严格按照 JSON 格式输出。"
        )),
    ]

    response = llm.invoke(messages)
    content = response.content

    # Extract JSON from the response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    data = json.loads(content.strip())

    return {
        "story_bible": data["story_bible"],
        "chapter_outlines": data["chapter_outlines"],
        "current_chapter": 0,
    }
