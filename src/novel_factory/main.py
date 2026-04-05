"""CLI entry point for the Novel Factory multi-agent pipeline."""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from novel_factory.graph import build_graph
from novel_factory.state import NovelState


def _get_llm(model: str):
    """Instantiate the appropriate LangChain chat model."""
    if model.startswith("claude"):
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model, max_tokens=8192)
    else:
        from langchain_openai import ChatOpenAI
        base_url = os.environ.get("OPENAI_BASE_URL")
        kwargs = {"model": model, "max_tokens": 8192}
        if base_url:
            kwargs["base_url"] = base_url
        return ChatOpenAI(**kwargs)


def _save_outputs(completed_chapters: list[dict], output_dir: Path):
    """Write each chapter and the full novel to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    full_parts: list[str] = []
    for ch in completed_chapters:
        num = ch["chapter_number"]
        title = ch["title"]
        text = ch["text"]

        chapter_file = output_dir / f"chapter_{num:02d}.md"
        chapter_file.write_text(
            f"# {title}\n\n{text}\n",
            encoding="utf-8",
        )
        print(f"  ✓ 已保存 {chapter_file}")
        full_parts.append(f"# {title}\n\n{text}")

    full_novel = output_dir / "full_novel.md"
    full_novel.write_text("\n\n---\n\n".join(full_parts) + "\n", encoding="utf-8")
    print(f"  ✓ 已保存完整小说 → {full_novel}")

    # Also dump the story bible
    if completed_chapters:
        bible_file = output_dir / "story_bible.json"
        bible_file.write_text(
            json.dumps(
                completed_chapters[0].get("story_bible", {}),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Novel Factory — AI Multi-Agent Novel Writing Pipeline",
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Creative inspiration / premise for the novel",
    )
    parser.add_argument(
        "-c", "--chapters",
        type=int,
        default=5,
        help="Number of chapters to generate (default: 5)",
    )
    parser.add_argument(
        "-m", "--model",
        default=os.environ.get("OPENAI_MODEL", "gpt-4o"),
        help="LLM model name (default: env OPENAI_MODEL or gpt-4o)",
    )
    parser.add_argument(
        "--max-revisions",
        type=int,
        default=3,
        help="Max revision rounds per scene beat (default: 3)",
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="./output",
        help="Directory for generated novel files (default: ./output)",
    )
    args = parser.parse_args()

    # Validate API keys
    if args.model.startswith("claude"):
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("错误：使用 Claude 模型需要设置 ANTHROPIC_API_KEY 环境变量。")
            sys.exit(1)
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            print("错误：使用 OpenAI 模型需要设置 OPENAI_API_KEY 环境变量。")
            sys.exit(1)

    print(f"🏭 Novel Factory 启动")
    print(f"   模型: {args.model}")
    print(f"   章节: {args.chapters}")
    print(f"   灵感: {args.input[:80]}{'...' if len(args.input) > 80 else ''}")
    print()

    llm = _get_llm(args.model)
    app = build_graph(llm)

    initial_state: NovelState = {
        "user_input": args.input,
        "story_bible": {},
        "chapter_outlines": [{}] * args.chapters,  # placeholder outlines
        "current_chapter": 0,
        "current_beats": [],
        "current_beat_index": 0,
        "draft_text": "",
        "editor_feedback": "",
        "editor_approved": False,
        "revision_count": 0,
        "max_revisions": args.max_revisions,
        "past_summaries": [],
        "completed_scenes": [],
        "completed_chapters": [],
    }

    print("📐 阶段 1/5: 世界观构建中 (Chief Architect)...")

    # Stream events so we can show progress
    current_node = ""
    final_state = None
    for event in app.stream(initial_state, {"recursion_limit": 150}):
        for node_name, node_output in event.items():
            if node_name != current_node:
                current_node = node_name
                _print_progress(node_name, node_output)
            final_state = {**initial_state, **(final_state or {}), **node_output}

    if not final_state:
        print("错误：流水线未产生任何输出。")
        sys.exit(1)

    print()
    print("=" * 60)
    print("📖 小说生成完成！正在保存文件...")
    _save_outputs(final_state.get("completed_chapters", []), Path(args.output_dir))
    print("=" * 60)
    print("✅ 全部完成！")


def _print_progress(node_name: str, output: dict):
    """Print a human-friendly progress line for each node activation."""
    labels = {
        "architect": "📐 世界观构建完成 → 开始细化章节...",
        "outliner": "📝 章节细化完成 → 开始撰写正文...",
        "novelist": "✍️  正在撰写场景草稿...",
        "editor": "🔍 正在审稿...",
        "advance_beat": "✅ 场景通过审核，进入下一场景...",
        "summarizer": "📋 章节完成，生成摘要...",
    }
    label = labels.get(node_name, f"🔄 {node_name}")

    # Extra context for specific nodes
    if node_name == "editor" and "editor_approved" in output:
        status = "通过 ✓" if output["editor_approved"] else f"需修改 (第{output.get('revision_count', '?')}次)"
        label = f"🔍 审稿结果: {status}"
    elif node_name == "summarizer" and "completed_chapters" in output:
        ch = output["completed_chapters"][-1] if output["completed_chapters"] else {}
        label = f"📋 第{ch.get('chapter_number', '?')}章「{ch.get('title', '')}」完成"

    print(f"  {label}")


if __name__ == "__main__":
    main()
