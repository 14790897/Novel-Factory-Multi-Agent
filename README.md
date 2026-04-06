# Novel-Factory Multi-Agent

基于 LangGraph 的长篇小说创作流水线系统。通过多个 AI Agent 协作，将小说创作拆解为：世界观规划 → 章节细化 → 正文撰写 → 逻辑审查 → 修改循环。

可选地启用“文风参考”模式：系统会为每个场景额外运行两个 Agent，先联网检索相关文章，再提炼成一个场景级文风 brief，供主笔模仿高层风格特征。

## 架构

```
architect → outliner → style_researcher? → style_analyst? → novelist → editor
                ↑                                       ↑            │
                │                                       └─ revise ───┤  (未通过审核)
                │                                                    │
                │                                     advance_beat ←─┘  (通过审核)
                │                                         │
                │                                    more beats?
                │                                         │
                │                      style_researcher? / novelist
                │                                         │
                │                                    summarizer
                │                                         │
                └────────────── more chapters? ───────────┘
                                                          │
                                                         END
```

| Agent | 职责 |
|-------|------|
| **Chief Architect** | 根据灵感生成设定集 (Story Bible) 和章节大纲 |
| **Chapter Outliner** | 将粗略大纲扩写为场景节拍 (Scene Beats) |
| **Style Researcher** | 检索并抓取与当前场景相关的参考文章 |
| **Style Analyst** | 从参考文章中提炼场景级文风 brief |
| **Novelist** | 根据场景节拍和角色卡片撰写正文草稿 |
| **Editor / Critic** | 对照设定集审查草稿的一致性和质量 |
| **Summarizer** | 为已完成章节生成剧情摘要，供后续章节参考 |

## 安装

```bash
cd "Novel-Factory Multi-Agent"
pip install -e .
```

## 配置

复制环境变量模板并填入 API Key：

```bash
cp .env.example .env
```

`.env` 配置项：

| 变量 | 说明 | 必填 |
|------|------|------|
| `OPENAI_API_KEY` | OpenAI / 兼容 API 的密钥 | 是（使用 OpenAI 兼容模型时） |
| `OPENAI_MODEL` | 默认模型名称 | 否，默认 `gpt-4o` |
| `OPENAI_BASE_URL` | 自定义 API 地址（支持 DeepSeek 等兼容接口） | 否 |
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 | 是（使用 Claude 模型时） |

## 使用

```bash
# 基本用法
python -m novel_factory.main -i "一个关于时间旅行者在末日废墟中寻找失落文明的故事" -c 3
novel-factory -i "一个关于时间旅行者在末日废墟中寻找失落文明的故事" -c 3
novel-factory -i "一个都市开后宫的故事" -c 3    
# 指定模型
python -m novel_factory.main -i "你的灵感" -c 5 -m claude-sonnet-4-6

# 全部参数
python -m novel_factory.main \
  -i "创意灵感" \
  -c 5 \
  -m deepseek-chat \
  --max-revisions 3 \
  --style-query "鲁迅杂文式冷峻观察" \
  --style-reference-limit 2 \
  -o ./output
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-i / --input` | 创意灵感 | 必填 |
| `-c / --chapters` | 章节数 | `5` |
| `-m / --model` | LLM 模型 | 环境变量 `OPENAI_MODEL` 或 `gpt-4o` |
| `--max-revisions` | 每场景最大修改次数 | `3` |
| `--style-query` | 启用文风参考检索，描述目标文风/文章类型 | 空 |
| `--style-reference-limit` | 每个场景抓取的参考文章数 | `2` |
| `-o / --output-dir` | 输出目录 | `./output` |

## 输出

生成的文件保存在 `output/` 目录：

```
output/
├── chapter_01_20260406_120000_1234.md
├── chapter_02_20260406_120000_1234.md
├── ...
├── full_novel_20260406_120000_1234.md
├── story_bible_20260406_120000_1234.json
└── novel_factory_20260406_120000_1234.log
```

## 项目结构

```
src/novel_factory/
├── state.py           # NovelState 全局状态定义
├── prompts.py         # Agent Prompt 模板
├── graph.py           # LangGraph 图编排与条件边
├── main.py            # CLI 入口
└── agents/
    ├── architect.py   # 世界观规划
    ├── outliner.py    # 章节细化
    ├── style_researcher.py # 检索参考文章
    ├── style_analyst.py    # 提炼文风 brief
    ├── novelist.py    # 主笔
    ├── editor.py      # 审稿
    └── summarizer.py  # 摘要
```
