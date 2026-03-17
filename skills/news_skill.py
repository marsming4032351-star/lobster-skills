"""
news_skill.py — 热点资讯速览，调用 Brave Search + Claude 摘要
"""
import re, os, sys, requests, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SKILL_NAME = "新闻速览"
SKILL_DESC = "搜索科技/AI/财经最新资讯，一句话摘要"
TRIGGERS   = ["/news", "/新闻", "/资讯"]
KEYWORDS   = ["最新消息", "今日新闻", "热点", "有什么新闻", "科技新闻", "AI新闻"]

logger = logging.getLogger(__name__)

_PREFIX   = re.compile(r'^(/news|/新闻|/资讯)\s*', re.IGNORECASE)
_BLOCKED  = ("zhihu.com", "baidu.com", "sogou.com", "bing.com")
_DEFAULT_QUERY = "AI科技 最新进展"


def _brave_search(query: str, count: int = 6) -> list[dict]:
    key = os.getenv("BRAVE_API_KEY", "")
    if not key:
        return []
    try:
        resp = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"Accept": "application/json", "X-Subscription-Token": key},
            params={"q": query, "count": count, "search_lang": "zh"},
            timeout=10,
        )
        resp.raise_for_status()
        results = resp.json().get("web", {}).get("results", [])
        return [r for r in results if not any(b in r.get("url", "") for b in _BLOCKED)]
    except Exception as e:
        logger.warning(f"[news_skill] Brave search failed: {e}")
        return []


def handle(user_text: str) -> str:
    from app.llm_client import call_anthropic
    query = _PREFIX.sub("", user_text.strip()).strip() or _DEFAULT_QUERY

    items = _brave_search(query)
    if not items:
        return f"❌ 暂时搜不到「{query}」相关资讯，请稍后再试。"

    numbered = "\n".join(
        f"[{i+1}] {it['title']}\n    {it.get('description','')[:80]}\n    {it['url']}"
        for i, it in enumerate(items)
    )
    try:
        summary = call_anthropic(
            system="你是资讯编辑，根据以下搜索结果，用3-5条中文简讯总结最重要的信息，每条一行，带序号，结尾附原文链接。",
            user=f"查询：{query}\n\n{numbered}",
            max_tokens=600,
        )
        return f"📰 {query} — 最新资讯\n\n{summary}"
    except Exception as e:
        # 降级：直接返回标题列表
        lines = [f"📰 {query} — 最新资讯\n"]
        for it in items[:4]:
            lines.append(f"· {it['title']}\n  {it['url']}")
        return "\n".join(lines)
