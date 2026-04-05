"""NovelState — the global state shared across all agents in the pipeline."""

from typing import TypedDict


class NovelState(TypedDict):
    # User's initial creative prompt / inspiration
    user_input: str

    # Global Story Bible: characters, world rules, core conflict, etc.
    story_bible: dict

    # High-level outlines for every chapter produced by the Architect
    chapter_outlines: list[dict]

    # Index of the chapter currently being written (0-based)
    current_chapter: int

    # Detailed scene beats for the current chapter
    current_beats: list[dict]

    # Index of the scene beat currently being drafted (0-based)
    current_beat_index: int

    # Raw draft text produced by the Novelist for the current beat
    draft_text: str

    # Feedback from the Editor on the current draft
    editor_feedback: str

    # Whether the Editor approved the current draft
    editor_approved: bool

    # How many revision rounds the current beat has gone through
    revision_count: int

    # Cap on revisions per beat to prevent infinite loops
    max_revisions: int

    # Plot summaries of all previously completed chapters
    past_summaries: list[str]

    # Finished scene texts within the current chapter
    completed_scenes: list[str]

    # Archive of fully completed chapters [{title, text, summary}, ...]
    completed_chapters: list[dict]
