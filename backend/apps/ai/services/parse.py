"""
从文本或图片中直接解析账单（不走对话）。对应原项目 ai/services 中的 parseBills 与 base.adapter.ts 的
BILL_PARSE_PROMPT / parseAIResponse。
"""
import json
import logging
import re
from datetime import date

from asgiref.sync import async_to_sync

from common.exceptions import BusinessError

from ..adapters import get_adapter
from .configs import resolve_ai_config

logger = logging.getLogger(__name__)

BILL_PARSE_PROMPT = """你是一个专业的记账助手。请从以下内容中提取所有的消费或收入记录。

对于每条记录，请提取：
- amount: 金额（数字，保留小数）
- type: 类型（expense=支出, income=收入）
- categoryName: 分类（餐饮/交通/购物/居住/娱乐/医疗/教育/工资/理财/其他）
- description: 简短描述（10字以内）
- date: 日期（YYYY-MM-DD 格式，如无法确定则使用今天日期）

请以 JSON 数组格式返回，例如：
[{"amount": 25.6, "type": "expense", "categoryName": "餐饮", "description": "星巴克咖啡", "date": "2026-01-25"}]

注意：
1. 如果无法识别任何账单信息，返回空数组 []
2. 只返回 JSON 数组，不要返回任何其他内容
3. 金额必须是正数
4. 分类必须是上述列表中的一个

用户输入："""

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_ai_response(text: str) -> list[dict]:
    """从模型回复里取出 JSON 数组并清洗，不合法的条目直接丢弃。"""
    match = re.search(r"\[[\s\S]*\]", text or "")  # 贪婪匹配：描述里出现 ] 也不会被截断
    if not match:
        return []
    try:
        items = json.loads(match.group(0))
    except ValueError:
        return []
    if not isinstance(items, list):
        return []

    today = date.today().isoformat()
    bills = []
    for item in items:
        if not isinstance(item, dict):
            continue
        amount = item.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
            continue
        if item.get("type") not in ("income", "expense"):
            continue
        if not isinstance(item.get("categoryName"), str) or not isinstance(item.get("description"), str):
            continue
        day = item.get("date")
        bills.append({
            "amount": round(float(amount), 2),
            "type": item["type"],
            "category_name": item["categoryName"],
            "description": item["description"][:100],
            # 模型偶尔会给出不合法的日期，退回今天，避免前端保存时才报错
            "date": day if isinstance(day, str) and DATE_RE.match(day) else today,
        })
    return bills


def parse_bills(user, content: str, input_type: str = "text", config_id=None) -> list[dict]:
    config = resolve_ai_config(user, config_id)
    if input_type == "image" and not config.supports_vision:
        raise BusinessError("当前模型不支持图片识别")

    if input_type == "image":
        message = {"role": "user", "content": [
            {"type": "image", "data": content, "media_type": "image/jpeg"},
            {"type": "text", "text": BILL_PARSE_PROMPT.rstrip("：")},
        ]}
    else:
        message = {"role": "user", "content": f"{BILL_PARSE_PROMPT}\n{content}"}

    adapter = get_adapter(config)
    try:
        response = async_to_sync(adapter.chat)([message], [])
    except Exception as exc:
        logger.warning("账单解析失败", exc_info=True)
        raise BusinessError(f"账单解析失败: {exc}", status=502) from exc

    bills = parse_ai_response(response.content or "")
    logger.info("账单解析完成，识别到 %d 条", len(bills))
    return bills
