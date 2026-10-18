"""
AI 可调用的工具定义（JSON Schema）。对应原项目 ai/tools/tool-definitions.ts。
参数细节请对照原文件补全。
"""

TOOLS = [
    {
        "name": "create_bills",
        "description": "创建一条或多条账单记录",
        "parameters": {
            "type": "object",
            "properties": {
                "bills": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "amount": {"type": "number", "description": "金额，正数"},
                            "type": {"type": "string", "enum": ["income", "expense"]},
                            "categoryName": {"type": "string", "description": "分类名称"},
                            "description": {"type": "string"},
                            "date": {"type": "string", "description": "YYYY-MM-DD"},
                        },
                        "required": ["amount", "type", "categoryName", "date"],
                    },
                },
            },
            "required": ["bills"],
        },
    },
    {
        "name": "query_bills",
        "description": "按条件查询账单",
        "parameters": {
            "type": "object",
            "properties": {
                "type": {"type": "string", "enum": ["income", "expense"]},
                "categoryName": {"type": "string"},
                "startDate": {"type": "string"},
                "endDate": {"type": "string"},
                "limit": {"type": "integer", "default": 20},
            },
        },
    },
    {
        "name": "delete_bills",
        "description": "删除指定 ID 的账单",
        "parameters": {
            "type": "object",
            "properties": {"ids": {"type": "array", "items": {"type": "integer"}}},
            "required": ["ids"],
        },
    },
    {
        "name": "get_statistics",
        "description": "获取指定时间范围内的收支统计",
        "parameters": {
            "type": "object",
            "properties": {
                "startDate": {"type": "string"},
                "endDate": {"type": "string"},
            },
        },
    },
]
