"""
分页：输出 {items, pagination{page, limit, total, totalPages, hasNext, hasPrev}}，
与原项目 PaginatedResponse 保持一致。
"""
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class PagePagination(PageNumberPagination):
    page_query_param = "page"
    page_size_query_param = "limit"
    max_page_size = 200

    def get_paginated_response(self, data):
        page = self.page
        return Response({
            "items": data,
            "pagination": {
                "page": page.number,
                "limit": page.paginator.per_page,
                "total": page.paginator.count,
                "total_pages": page.paginator.num_pages,
                "has_next": page.has_next(),
                "has_prev": page.has_previous(),
            },
        })

    def get_paginated_response_schema(self, schema):
        return {
            "type": "object",
            "properties": {
                "items": schema,
                "pagination": {"type": "object"},
            },
        }
