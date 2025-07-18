from fastapi import Response

from app.models import Pagination


def set_pagination_headers(response: Response, meta: Pagination) -> None:
    response.headers["X-Total-Count"] = str(meta.total)
    response.headers["X-Page"] = str(meta.page)
    response.headers["X-Page-Size"] = str(meta.page_size)
