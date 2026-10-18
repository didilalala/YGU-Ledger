"""
执行 AI 发起的工具调用。对应原项目 ai/services/tool-executor.service.ts。
每个工具返回 {success, data, message}，作为 tool 消息回传给模型，同时通过 tool_result 事件推给前端。
"""
import logging

from django.db.models import Q

from apps.bills.models import Bill
from apps.bills.services import filter_by_date, get_statistics
from apps.categories.models import Category

logger = logging.getLogger(__name__)

MAX_QUERY_LIMIT = 50


def _categories(user):
    return list(Category.objects.filter(Q(user=user) | Q(user__isnull=True)))


def _create_bills(user, args):
    """
    只做数据补全（categoryName → categoryId），不入库。
    账单由前端展示给用户确认后再保存，与原项目行为一致。
    """
    categories = _categories(user)
    bills = []
    for bill in args.get("bills") or []:
        # 同名时用户自己的分类优先于系统默认分类
        matches = [c for c in categories if c.name == bill.get("categoryName") and c.type == bill.get("type")]
        category = next((c for c in matches if c.user_id), matches[0] if matches else None)
        bills.append({
            "amount": float(bill["amount"]),
            "type": bill["type"],
            "description": bill.get("description") or "",
            "categoryName": bill.get("categoryName"),
            "categoryId": category.id if category else None,
            "categoryIcon": category.icon if category else None,
            "date": bill["date"],
        })
    return {"success": True, "data": {"bills": bills}, "message": f"识别到 {len(bills)} 条账单"}


def _query_bills(user, args):
    qs = Bill.objects.filter(user=user).select_related("category")
    if args.get("type"):
        qs = qs.filter(type=args["type"])
    if args.get("categoryName"):
        category_ids = [c.id for c in _categories(user) if c.name == args["categoryName"]]
        qs = qs.filter(category_id__in=category_ids)
    qs = filter_by_date(qs, args.get("startDate"), args.get("endDate"))
    limit = min(int(args.get("limit") or 20), MAX_QUERY_LIMIT)
    total = qs.count()
    items = [{
        "id": b.id,
        "amount": float(b.amount),
        "type": b.type,
        "description": b.description,
        "date": b.date.isoformat(),
        "categoryName": b.category.name if b.category else None,
        "categoryIcon": b.category.icon if b.category else None,
    } for b in qs.order_by("-date", "-id")[:limit]]
    return {"success": True, "data": {"items": items, "total": total},
            "message": f"查询到 {len(items)} 条账单"}


def _delete_bills(user, args):
    results = []
    for bill_id in args.get("billIds") or []:
        # 只能删除自己的账单，别人的 ID 与不存在的 ID 返回同样的结果
        deleted, _ = Bill.objects.filter(user=user, id=bill_id).delete()
        results.append({"id": bill_id, "deleted": bool(deleted),
                        **({} if deleted else {"error": "账单不存在"})})
    count = sum(r["deleted"] for r in results)
    return {"success": True, "data": {"results": results, "successCount": count},
            "message": f"成功删除 {count} 条账单"}


def _get_statistics(user, args):
    stats = get_statistics(user, start_date=args.get("startDate"), end_date=args.get("endDate"))
    return {"success": True, "data": stats, "message": "统计数据获取成功"}


HANDLERS = {
    "create_bills": _create_bills,
    "query_bills": _query_bills,
    "delete_bills": _delete_bills,
    "get_statistics": _get_statistics,
}


def execute(user, name: str, arguments: dict) -> dict:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"success": False, "data": None, "message": f"未知工具: {name}"}
    try:
        return handler(user, arguments or {})
    except Exception as exc:  # 工具失败不应中断对话，把错误交给模型处理
        logger.warning("工具 %s 执行失败: %s", name, exc)
        return {"success": False, "data": None, "message": f"{name} 执行失败: {exc}"}
