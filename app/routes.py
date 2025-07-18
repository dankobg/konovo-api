from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Path, Response

from app.dependencies import (
    extract_jwt,
    get_auth_service,
    get_pagination_filters,
    get_product_filters,
    get_product_service,
)
from app.pagination import set_pagination_headers

from .models import (
    KonovoApiError,
    KonovoValidationError,
    LoginRequest,
    PaginatedProducts,
    PaginationFilters,
    Product,
    ProductFilters,
    TokenResponse,
)
from .services import (
    AuthService,
    ProductService,
)

response_internal_500: dict[int, dict[str, Any]] = {
    500: {"model": KonovoApiError, "description": "Internal Server Error"}
}


router = APIRouter()


@router.post(
    "/auth/login",
    operation_id="login",
    response_model=TokenResponse,
    responses={
        **response_internal_500,
        401: {"model": KonovoApiError, "description": "Unauthorized access"},
        422: {"model": KonovoValidationError, "description": "Validation error"},
    },
)
async def login(
    login_req: Annotated[LoginRequest, Body(title="Login credentials")],
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await auth_service.login(login_req=login_req)


@router.get(
    "/products",
    operation_id="list_products",
    response_model=PaginatedProducts,
    responses={
        **response_internal_500,
        401: {"model": KonovoApiError, "description": "Unauthorized access"},
        422: {"model": KonovoValidationError, "description": "Validation error"},
    },
)
async def list_products(
    response: Response,
    filters: ProductFilters = Depends(get_product_filters),
    pagination: PaginationFilters = Depends(get_pagination_filters),
    jwt: str = Depends(extract_jwt),
    product_service: ProductService = Depends(get_product_service),
) -> PaginatedProducts:
    paginated_products = await product_service.list_products(
        jwt=jwt, filters=filters, pagination=pagination
    )
    set_pagination_headers(response, paginated_products.meta)
    return paginated_products


@router.get(
    "/products/{product_id}",
    operation_id="get_product_by_id",
    response_model=Product,
    responses={
        **response_internal_500,
        401: {"model": KonovoApiError, "description": "Unauthorized access"},
        404: {"model": KonovoApiError, "description": "Product not found"},
        422: {
            "model": KonovoValidationError,
            "description": "Validation error",
        },
    },
)
async def get_product_by_id(
    product_id: Annotated[int, Path(title="The ID of the product to get")],
    jwt: str = Depends(extract_jwt),
    product_service: ProductService = Depends(get_product_service),
) -> Product:
    return await product_service.get_product_by_id(jwt=jwt, product_id=product_id)
