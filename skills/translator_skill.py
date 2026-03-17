"""
translator_skill.py — 中英互译，调用龙虾 LLM client
"""
import re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SKILL_NAME = "翻译助手"
SKILL_DESC = "中英互译，发送「翻译 xxx」或「translate xxx」即可"
TRIGGERS   = ["/翻译", "/translate", "/tr"]
KEYWORDS   = ["翻译", "translate", "用英文说", "用中文说", "怎么翻译"]

_PREFIX = re.compile(r'^(/翻译|/translate|/tr|翻译)\s*', re.IGNORECASE)


def _detect_lang(text: str) -> str:
    cjk = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    return "中文" if cjk / max(len(text), 1) > 0.2 else "英文"


def handle(user_text: str) -> str:
    from app.llm_client import call_anthropic
    content = _PREFIX.sub("", user_text.strip()).strip()
    if not content:
        return "用法：翻译 你好世界  或  /tr Hello World"
    src = _detect_lang(content)
    tgt = "英文" if src == "中文" else "中文"
    try:
        result = call_anthropic(
            system=f"你是专业翻译，将用户输入从{src}翻译成{tgt}，只输出译文，不加任何解释。",
            user=content,
            max_tokens=512,
        )
        arrow = "🇨🇳→🇺🇸" if src == "中文" else "🇺🇸→🇨🇳"
        return f"{arrow}\n{result.strip()}"
    except Exception as e:
        return f"❌ 翻译失败：{str(e)[:60]}"
