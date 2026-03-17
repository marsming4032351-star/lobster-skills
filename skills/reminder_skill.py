"""
reminder_skill.py — 定时提醒，基于 APScheduler，到点飞书推送
"""
import re, sys, os, datetime, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SKILL_NAME = "定时提醒"
SKILL_DESC = "设置倒计时提醒，到点飞书推送。例：提醒我 30分钟后 开会"
TRIGGERS   = ["/remind", "/提醒"]
KEYWORDS   = ["分钟后提醒", "小时后提醒", "提醒我", "minutes后", "mins后"]

_PREFIX  = re.compile(r'^(/remind|/提醒)\s*', re.IGNORECASE)
_TIME_RE = re.compile(r'(\d+)\s*(分钟|分|min|mins|minutes|小时|时|hour|hours|h)', re.IGNORECASE)

_reminders: list = []
_lock = threading.Lock()


def _fire(receive_id: str, receive_id_type: str, msg: str):
    try:
        from app.feishu import send_message
        send_message(receive_id, receive_id_type, f"⏰ 提醒：{msg}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"[reminder] send failed: {e}")


def handle(user_text: str, receive_id: str = "", receive_id_type: str = "open_id") -> str:
    text = _PREFIX.sub("", user_text.strip()).strip()
    if not text:
        return "用法：提醒我 30分钟后 开会\n或：/remind 1小时后 吃药"

    m = _TIME_RE.search(text)
    if not m:
        return "❌ 请指定时间，例：提醒我 30分钟后 开会"

    amount = int(m.group(1))
    unit   = m.group(2)
    if unit in ("小时", "时", "hour", "hours", "h"):
        seconds = amount * 3600
        label   = f"{amount}小时"
    else:
        seconds = amount * 60
        label   = f"{amount}分钟"

    # 提取提醒内容（时间表达式之后的文字）
    content = text[m.end():].strip("后 ,，").strip() or text

    if not receive_id:
        return "❌ 无法获取用户 ID，提醒设置失败。"

    fire_at = datetime.datetime.now() + datetime.timedelta(seconds=seconds)
    t = threading.Timer(seconds, _fire, args=(receive_id, receive_id_type, content))
    t.daemon = True
    t.start()

    with _lock:
        _reminders.append({"at": fire_at.strftime("%H:%M:%S"), "msg": content})

    return f"✅ 已设置提醒！\n⏱ {label}后（{fire_at.strftime('%H:%M')}）提醒你：{content}"
