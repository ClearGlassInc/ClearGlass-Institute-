#!/usr/bin/env python3
"""
Growth OS: compliant social growth analytics and drafting assistant.

This tool analyzes post history and comment history, scores what is working,
recommends posting windows, flags high-value comments, generates post variants,
and proposes simple A/B tests. It does not auto-post, auto-engage, or evade
platform controls.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_TOPICS = ["AI", "cybersecurity", "policy", "finance", "Ontario"]
DEFAULT_REPLY_PATTERNS = [
    "Exactly. The real issue is {insight}.",
    "That is the point most people miss: {insight}.",
    "Agreed in part. The stronger conclusion is {insight}.",
    "People keep debating the surface. The underlying problem is {insight}.",
]
DEFAULT_POST_PATTERNS = [
    "{hook}\n\nMost companies are not losing because of effort.\nThey are losing because {insight}.\n\nThat is where systems, security, and disciplined execution decide who scales.\n\nWhat are you seeing from inside the business?",
    "{hook}\n\nThe visible problem gets attention.\nThe structural problem does the damage.\n\nIn practice, {insight}.\n\nWhat do operators keep underestimating here?",
    "{hook}\n\nEveryone wants AI upside.\nFew want to fix the workflow, governance, and security debt underneath it.\n\n{insight}\n\nWhat breaks first when leadership ignores that?",
    "{hook}\n\nThis is not a tooling issue.\nIt is an operating model issue.\n\n{insight}\n\nWhere do you see the drag most clearly?",
    "{hook}\n\nThe companies that win are not always louder.\nThey are cleaner, faster, and harder to break.\n\n{insight}\n\nDo you think most teams are optimizing the right layer?",
]

NEGATIVE_KEYWORDS = {"wrong", "false", "source", "prove", "doubt", "disagree", "bs", "nonsense"}
ENGAGEMENT_KEYWORDS = {"exactly", "agree", "finally", "true", "important", "needed", "fact"}


@dataclass
class PostRecord:
    post_id: str
    created_at: str
    text: str
    topic: str
    hook_style: str
    structure: str
    cta: str
    tone: str
    impressions: float
    likes: float
    replies: float
    reposts: float
    profile_visits: float
    follows_gained: float

    @property
    def created_dt(self) -> datetime:
        return parse_datetime(self.created_at)

    @property
    def weekday(self) -> str:
        return self.created_dt.strftime("%A")

    @property
    def hour(self) -> int:
        return self.created_dt.hour

    @property
    def length_bucket(self) -> str:
        n = len(self.text or "")
        if n < 120:
            return "short"
        if n < 240:
            return "medium"
        return "long"


@dataclass
class CommentRecord:
    comment_id: str
    post_id: str
    created_at: str
    author: str
    body: str
    author_followers: float = 0
    likes: float = 0
    replies_count: float = 0

    @property
    def created_dt(self) -> datetime:
        return parse_datetime(self.created_at)


def parse_datetime(value: str) -> datetime:
    value = (value or "").strip()
    if not value:
        return datetime.min
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min


def read_table(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            for key in ("items", "posts", "comments", "rows", "data"):
                if key in data and isinstance(data[key], list):
                    return data[key]
            return [data]
        return data
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_float(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace(",", "")
    if text == "":
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def load_posts(path: Path) -> List[PostRecord]:
    rows = read_table(path)
    posts: List[PostRecord] = []
    for i, row in enumerate(rows, start=1):
        posts.append(
            PostRecord(
                post_id=str(row.get("post_id") or row.get("id") or i),
                created_at=str(row.get("created_at") or row.get("date") or ""),
                text=str(row.get("text") or row.get("body") or ""),
                topic=str(row.get("topic") or "unknown"),
                hook_style=str(row.get("hook_style") or row.get("hook") or "unknown"),
                structure=str(row.get("structure") or "standard"),
                cta=str(row.get("cta") or "none"),
                tone=str(row.get("tone") or "neutral"),
                impressions=normalize_float(row.get("impressions")),
                likes=normalize_float(row.get("likes")),
                replies=normalize_float(row.get("replies")),
                reposts=normalize_float(row.get("reposts") or row.get("shares")),
                profile_visits=normalize_float(row.get("profile_visits")),
                follows_gained=normalize_float(row.get("follows_gained") or row.get("followers_gained")),
            )
        )
    return posts


def load_comments(path: Optional[Path]) -> List[CommentRecord]:
    if path is None or not path.exists():
        return []
    rows = read_table(path)
    comments: List[CommentRecord] = []
    for i, row in enumerate(rows, start=1):
        comments.append(
            CommentRecord(
                comment_id=str(row.get("comment_id") or row.get("id") or i),
                post_id=str(row.get("post_id") or ""),
                created_at=str(row.get("created_at") or row.get("date") or ""),
                author=str(row.get("author") or "unknown"),
                body=str(row.get("body") or row.get("text") or ""),
                author_followers=normalize_float(row.get("author_followers")),
                likes=normalize_float(row.get("likes")),
                replies_count=normalize_float(row.get("replies_count") or row.get("replies")),
            )
        )
    return comments


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def score_post(post: PostRecord) -> Dict[str, float]:
    impressions = max(post.impressions, 1.0)
    interactions = post.likes + (post.replies * 2.5) + (post.reposts * 4.0)
    value_actions = (post.profile_visits * 2.0) + (post.follows_gained * 8.0)
    reach_score = (interactions + value_actions) / math.sqrt(impressions)
    engagement_rate = safe_div(interactions, impressions)
    follow_conversion = safe_div(post.follows_gained, max(post.profile_visits, 1.0))
    impression_to_follow = safe_div(post.follows_gained, impressions)
    composite = (engagement_rate * 1000) + (follow_conversion * 120) + (impression_to_follow * 5000)
    return {
        "reach_score": round(reach_score, 4),
        "engagement_rate": round(engagement_rate, 6),
        "follow_conversion": round(follow_conversion, 6),
        "impression_to_follow": round(impression_to_follow, 6),
        "composite_score": round(composite, 4),
    }


def summarize_dimension(posts: List[PostRecord], accessor) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[float]] = defaultdict(list)
    counts: Counter = Counter()
    for post in posts:
        key = accessor(post) or "unknown"
        grouped[key].append(score_post(post)["composite_score"])
        counts[key] += 1
    ranked = []
    for key, scores in grouped.items():
        ranked.append(
            {
                "name": key,
                "posts": counts[key],
                "avg_composite_score": round(sum(scores) / len(scores), 4),
                "median_composite_score": round(statistics.median(scores), 4),
            }
        )
    return sorted(ranked, key=lambda x: (x["avg_composite_score"], x["posts"]), reverse=True)


def recommend_windows(posts: List[PostRecord], top_n: int = 5) -> List[Dict[str, Any]]:
    slots: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    for post in posts:
        slots[(post.weekday, post.hour)].append(score_post(post)["composite_score"])
    ranked = []
    for (weekday, hour), scores in slots.items():
        ranked.append(
            {
                "weekday": weekday,
                "hour": hour,
                "avg_score": round(sum(scores) / len(scores), 4),
                "sample_size": len(scores),
            }
        )
    ranked.sort(key=lambda x: (x["avg_score"], x["sample_size"]), reverse=True)
    return ranked[:top_n]


def find_high_value_comments(comments: List[CommentRecord], limit: int = 10) -> List[Dict[str, Any]]:
    scored = []
    for comment in comments:
        body_lower = comment.body.lower()
        keyword_bonus = sum(3 for word in NEGATIVE_KEYWORDS if word in body_lower)
        keyword_bonus += sum(2 for word in ENGAGEMENT_KEYWORDS if word in body_lower)
        length_bonus = min(len(comment.body) / 80.0, 4.0)
        score = (
            comment.author_followers * 0.01
            + comment.likes * 2.0
            + comment.replies_count * 3.0
            + keyword_bonus
            + length_bonus
        )
        scored.append(
            {
                "comment_id": comment.comment_id,
                "post_id": comment.post_id,
                "author": comment.author,
                "body": comment.body,
                "priority_score": round(score, 2),
                "author_followers": comment.author_followers,
                "likes": comment.likes,
                "replies_count": comment.replies_count,
            }
        )
    return sorted(scored, key=lambda x: x["priority_score"], reverse=True)[:limit]


def strongest_text_signal(posts: List[PostRecord], topic: str) -> str:
    topic_posts = [p for p in posts if p.topic.lower() == topic.lower()]
    if not topic_posts:
        return f"{topic} is being handled with weak systems, loose process, and avoidable friction"
    best = max(topic_posts, key=lambda p: score_post(p)["composite_score"])
    text = re.sub(r"\s+", " ", best.text).strip()
    fragments = re.split(r"[.!?]", text)
    cleaned = [f.strip() for f in fragments if len(f.strip()) > 20]
    if cleaned:
        sentence = cleaned[0]
        return sentence[0].lower() + sentence[1:] if len(sentence) > 1 else sentence.lower()
    return f"{topic} is being handled with weak systems, loose process, and avoidable friction"


def build_hook(topic: str, hook_style: str) -> str:
    topic_clean = topic.strip()
    options = {
        "contrarian": f"Most companies do not have a {topic_clean} problem.",
        "insight": f"The hidden drag in {topic_clean} is not where most teams are looking.",
        "story": f"I have watched smart teams lose hours to avoidable {topic_clean} friction.",
        "warning": f"The next serious failure in {topic_clean} will not look obvious at first.",
        "future trend": f"The companies that master {topic_clean} will pull away faster than people expect.",
        "hard truth": f"The hard truth about {topic_clean}: effort is not the bottleneck.",
        "authority": f"From an operator’s seat, the biggest {topic_clean} failure is usually architectural.",
        "mistake": f"The biggest mistake in {topic_clean} is confusing activity with control.",
        "myth-busting": f"Myth: more tooling automatically fixes {topic_clean}.",
        "challenge": f"I challenge every operator to audit their {topic_clean} workflow honestly.",
    }
    return options.get(hook_style.lower(), f"Here is the real problem with {topic_clean}.")


def generate_variants(posts: List[PostRecord], topics: List[str], identity: Dict[str, Any], variants_per_topic: int = 5) -> List[Dict[str, Any]]:
    top_hooks = summarize_dimension(posts, lambda p: p.hook_style)
    preferred_hook_styles = [row["name"] for row in top_hooks[:5]] or ["contrarian", "hard truth", "warning", "insight", "authority"]
    variants = []
    for topic in topics:
        insight = strongest_text_signal(posts, topic)
        for idx in range(min(variants_per_topic, len(DEFAULT_POST_PATTERNS))):
            hook_style = preferred_hook_styles[idx % len(preferred_hook_styles)]
            hook = build_hook(topic, hook_style)
            text = DEFAULT_POST_PATTERNS[idx].format(hook=hook, insight=insight)
            text += (
                f"\n\n— {identity.get('title', 'Software Architect')} | "
                f"{identity.get('company', 'ClearGlassInc')} | "
                f"{identity.get('location', 'NYC')}"
            )
            variants.append(
                {
                    "topic": topic,
                    "hook_style": hook_style,
                    "variant_number": idx + 1,
                    "text": text.strip(),
                }
            )
    return variants


def generate_reply_derivatives(comments: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, str]]:
    derivatives = []
    for item in comments[:limit]:
        body = re.sub(r"\s+", " ", item["body"]).strip()
        body = re.sub(r"^[\"'“”]+|[\"'“”]+$", "", body)
        if len(body) > 180:
            body = body[:177] + "..."
        insight = body[0].lower() + body[1:] if len(body) > 1 else body.lower()
        template = DEFAULT_REPLY_PATTERNS[len(derivatives) % len(DEFAULT_REPLY_PATTERNS)]
        reply = template.format(insight=insight)
        new_post = (
            "Most people react to the surface.\n\n"
            f"The stronger point is this: {insight}.\n\n"
            "That is where disciplined operators separate signal from noise.\n\n"
            "What are you seeing on the ground?"
        )
        derivatives.append(
            {
                "source_comment_id": item["comment_id"],
                "reply_draft": reply,
                "follow_up_post": new_post,
            }
        )
    return derivatives


def ab_test_suggestions(posts: List[PostRecord]) -> List[Dict[str, Any]]:
    tests = []
    for label, accessor in [
        ("hook_style", lambda p: p.hook_style),
        ("length_bucket", lambda p: p.length_bucket),
        ("cta", lambda p: p.cta),
        ("tone", lambda p: p.tone),
    ]:
        ranked = summarize_dimension(posts, accessor)
        if len(ranked) >= 2:
            winner = ranked[0]
            loser = ranked[-1]
            tests.append(
                {
                    "dimension": label,
                    "winner": winner["name"],
                    "winner_score": winner["avg_composite_score"],
                    "loser": loser["name"],
                    "loser_score": loser["avg_composite_score"],
                    "recommendation": f"Test more {winner['name']} against {loser['name']} for {label}.",
                }
            )
    return tests


def build_report(
    posts: List[PostRecord],
    comments: List[CommentRecord],
    identity: Dict[str, Any],
    topics: List[str],
) -> Dict[str, Any]:
    scored_posts = [{**asdict(post), **score_post(post)} for post in posts]
    top_posts = sorted(scored_posts, key=lambda x: x["composite_score"], reverse=True)[:10]
    high_value_comments = find_high_value_comments(comments)
    report = {
        "summary": {
            "total_posts": len(posts),
            "total_comments": len(comments),
            "avg_impressions": round(statistics.mean([p.impressions for p in posts]), 2) if posts else 0,
            "avg_follows_gained": round(statistics.mean([p.follows_gained for p in posts]), 2) if posts else 0,
        },
        "top_posts": top_posts,
        "topic_rankings": summarize_dimension(posts, lambda p: p.topic),
        "hook_rankings": summarize_dimension(posts, lambda p: p.hook_style),
        "structure_rankings": summarize_dimension(posts, lambda p: p.structure),
        "cta_rankings": summarize_dimension(posts, lambda p: p.cta),
        "tone_rankings": summarize_dimension(posts, lambda p: p.tone),
        "recommended_windows": recommend_windows(posts),
        "high_value_comments": high_value_comments,
        "reply_derivatives": generate_reply_derivatives(high_value_comments),
        "ab_tests": ab_test_suggestions(posts),
        "generated_variants": generate_variants(posts, topics, identity),
    }
    return report


def markdown_report(report: Dict[str, Any], identity: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Growth OS Report")
    lines.append("")
    lines.append(f"**Identity:** {identity.get('title', 'Operator')} at {identity.get('company', 'Company')} ({identity.get('location', 'Location')})")
    lines.append("")
    summary = report["summary"]
    lines.append("## Summary")
    lines.append(f"- Total posts analyzed: {summary['total_posts']}")
    lines.append(f"- Total comments analyzed: {summary['total_comments']}")
    lines.append(f"- Avg impressions: {summary['avg_impressions']}")
    lines.append(f"- Avg follows gained: {summary['avg_follows_gained']}")
    lines.append("")
    for section, title in [
        ("topic_rankings", "Top Topics"),
        ("hook_rankings", "Top Hooks"),
        ("structure_rankings", "Top Structures"),
        ("cta_rankings", "Top CTAs"),
        ("tone_rankings", "Top Tones"),
    ]:
        lines.append(f"## {title}")
        for row in report[section][:5]:
            lines.append(f"- {row['name']}: avg {row['avg_composite_score']} across {row['posts']} posts")
        lines.append("")
    lines.append("## Best Posting Windows")
    for row in report["recommended_windows"]:
        lines.append(f"- {row['weekday']} at {row['hour']:02d}:00 — avg score {row['avg_score']} ({row['sample_size']} samples)")
    lines.append("")
    lines.append("## High-Value Comments To Hit Fast")
    for row in report["high_value_comments"][:5]:
        lines.append(f"- [{row['priority_score']}] @{row['author']}: {row['body']}")
    lines.append("")
    lines.append("## A/B Test Suggestions")
    for row in report["ab_tests"]:
        lines.append(f"- {row['recommendation']} Winner avg {row['winner_score']} vs loser avg {row['loser_score']}.")
    lines.append("")
    lines.append("## Draft Variants")
    for item in report["generated_variants"][:10]:
        lines.append(f"### {item['topic']} — {item['hook_style']} #{item['variant_number']}")
        lines.append(item["text"])
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_identity(path: Optional[Path]) -> Dict[str, Any]:
    default_identity = {
        "title": "Software Architect & COO",
        "company": "ClearGlassInc",
        "location": "NYC",
        "focus": ["AI automation", "cybersecurity", "legal/corporate workflows", "scalable systems"],
    }
    if path is None or not path.exists():
        return default_identity
    data = json.loads(path.read_text(encoding="utf-8"))
    default_identity.update(data)
    return default_identity


def parse_topics(raw: Optional[str]) -> List[str]:
    if not raw:
        return DEFAULT_TOPICS
    return [x.strip() for x in raw.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Growth OS analytics and drafting assistant")
    parser.add_argument("--posts", required=True, help="Path to posts CSV or JSON")
    parser.add_argument("--comments", help="Path to comments CSV or JSON")
    parser.add_argument("--identity", help="Path to identity JSON")
    parser.add_argument("--topics", help="Comma-separated topics for variant generation")
    parser.add_argument("--outdir", default="growth_os_output", help="Directory for report outputs")
    args = parser.parse_args()

    posts = load_posts(Path(args.posts))
    comments = load_comments(Path(args.comments) if args.comments else None)
    identity = load_identity(Path(args.identity) if args.identity else None)
    topics = parse_topics(args.topics)

    report = build_report(posts, comments, identity, topics)

    outdir = Path(args.outdir)
    ensure_dir(outdir)
    json_path = outdir / "growth_os_report.json"
    md_path = outdir / "growth_os_report.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(markdown_report(report, identity), encoding="utf-8")

    print(f"[+] Report written: {json_path}")
    print(f"[+] Report written: {md_path}")
    print("[+] Growth OS completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
