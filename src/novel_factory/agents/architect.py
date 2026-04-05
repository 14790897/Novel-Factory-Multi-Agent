"""Chief Architect Agent — generates the Story Bible and chapter outlines."""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.utils.json import parse_json_markdown

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

    data = parse_json_markdown(content)

    return {
        "story_bible": data["story_bible"],
        "chapter_outlines": data["chapter_outlines"],
        "current_chapter": 0,
    }
