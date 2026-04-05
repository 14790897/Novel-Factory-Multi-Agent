"""Editor / Critic Agent — reviews drafts against the Story Bible."""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from novel_factory.prompts import EDITOR_SYSTEM
from novel_factory.state import NovelState


def editor_node(state: NovelState, llm) -> dict:
    """Review the current draft and produce structured feedback."""
    beat = state["current_beats"][state["current_beat_index"]]
    story_bible = state["story_bible"]
    draft = state["draft_text"]

    messages = [
        SystemMessage(content=EDITOR_SYSTEM),
        HumanMessage(content=(
            f"## 待审稿件\n{draft}\n\n"
            f"## 场景节拍要求\n{json.dumps(beat, ensure_ascii=False, indent=2)}\n\n"
            f"## 设定集\n{json.dumps(story_bible, ensure_ascii=False, indent=2)}\n\n"
            f"请严格按 JSON 格式输出审稿意见。"
        )),
    ]

    response = llm.invoke(messages)
    content = response.content

    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]

    review = json.loads(content.strip())

    approved = review.get("approved", True)

    # Build human-readable feedback for the novelist
    feedback_lines = []
    if not approved:
        feedback_lines.append(f"整体评价：{review.get('summary', '')}")
        for issue in review.get("issues", []):
            feedback_lines.append(
                f"- [{issue.get('severity', '?')}] {issue.get('type', '?')}: "
                f"{issue.get('description', '')} → 建议：{issue.get('suggestion', '')}"
            )

    return {
        "editor_approved": approved,
        "editor_feedback": "\n".join(feedback_lines) if feedback_lines else "",
        "revision_count": state["revision_count"] + 1,
    }
