from typing import Annotated
from fastapi import Depends, Query, Request
from fastapi.security import HTTPAuthorizationCredentials
from app.auth import AuthorizationBearer
from app.models import PaginationFilters, ProductFilters
from app.services import AuthService, ProductService


bearer_token = AuthorizationBearer()


def extract_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_token),
) -> str:
    return credentials.credentials


def get_auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_product_service(request: Request) -> ProductService:
    return request.app.state.product_service


def get_product_filters(
    name: Annotated[str | None, Query(title="name filter", max_length=100)] = None,
    brand_ids: Annotated[list[str] | None, Query(title="brand ids filter")] = None,
    category_ids: Annotated[
        list[str] | None, Query(title="category ids filter")
    ] = None,
    brand: Annotated[str | None, Query(title="brand filter", max_length=100)] = None,
    category: Annotated[
        str | None, Query(title="category filter", max_length=100)
    ] = None,
    price_lt: Annotated[
        float | None, Query(title="price price_lt filter", min=0)
    ] = None,
    price_lte: Annotated[
        float | None, Query(title="price price_lte filter", min=0)
    ] = None,
    price_gt: Annotated[
        float | None, Query(title="price price_gt filter", min=0)
    ] = None,
    price_gte: Annotated[
        float | None, Query(title="price price_gte filter", min=0)
    ] = None,
    sort: Annotated[str | None, Query(title="sort by filter")] = None,
) -> ProductFilters:
    return ProductFilters(
        name=name,
        brand_ids=brand_ids,
        category_ids=category_ids,
        brand=brand,
        category=category,
        price_lt=price_lt,
        price_lte=price_lte,
        price_gt=price_gt,
        price_gte=price_gte,
        sort=sort,
    )


def get_pagination_filters(
    page: Annotated[int | None, Query(title="page", min=1)] = None,
    page_size: Annotated[int | None, Query(title="page_size", min=10)] = None,
) -> PaginationFilters:
    return PaginationFilters(page=page, page_size=page_size)
