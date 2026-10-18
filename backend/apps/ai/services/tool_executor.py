"""
执行 AI 发起的工具调用。对应原项目 ai/services/tool-executor.service.ts。
每个工具返回可 JSON 序列化的 dict，会作为 tool 消息回传给模型。
"""
from apps.bills.services import get_statistics


def _create_bills(user, args):
    # TODO: 按 categoryName 匹配分类（系统默认 + 用户自定义），创建账单，source="text"
    raise NotImplementedError


def _query_bills(user, args):
    # TODO: 复用 BillViewSet 的过滤逻辑，返回精简字段列表
    raise NotImplementedError


def _delete_bills(user, args):
    # TODO: 只能删除当前用户的账单，返回删除数量
    raise NotImplementedError


def _get_statistics(user, args):
    return get_statistics(user, start_date=args.get("startDate"), end_date=args.get("endDate"))


HANDLERS = {
    "create_bills": _create_bills,
    "query_bills": _query_bills,
    "delete_bills": _delete_bills,
    "get_statistics": _get_statistics,
}


def execute(user, name: str, arguments: dict) -> dict:
    handler = HANDLERS.get(name)
    if handler is None:
        return {"success": False, "error": f"未知工具: {name}"}
    try:
        return {"success": True, "data": handler(user, arguments)}
    except NotImplementedError:
        return {"success": False, "error": f"工具 {name} 尚未实现"}
    except Exception as exc:  # 工具失败不应中断对话，把错误交给模型处理
        return {"success": False, "error": str(exc)}
