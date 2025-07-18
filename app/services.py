import re

import httpx
from fastapi import status
from pydantic import TypeAdapter

from app.models import (
    LoginRequest,
    PaginatedProducts,
    Pagination,
    PaginationFilters,
    Product,
    ProductFilters,
    TokenResponse,
)

from .errors import AuthenticationError, NotFoundError, UnavailableError

KONOVO_BASE_URL = "https://zadatak.konovo.rs"
KONOVO_LOGIN_PATH = "/login"
KONOVO_PRODUCTS_PATH = "/products"


class AuthService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def login(self, login_req: LoginRequest) -> TokenResponse:
        try:
            res = await self.client.post(
                url=KONOVO_LOGIN_PATH, json=login_req.model_dump()
            )
            res.raise_for_status()
            token_resp = TokenResponse.model_validate(res.json())
            return token_resp
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                raise AuthenticationError(
                    code="auth_token_invalid",
                    message="Not authenticated",
                    detail="Invalid credentials",
                )
        except httpx.RequestError:
            raise UnavailableError(
                code="service_unavailable",
                message="External service unavailable right now",
                detail="Please try again later",
            )
        raise


class ProductService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    def auth_headers(self, jwt: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {jwt}"}

    def adjust_product_price_for_monitors(self, prod: Product) -> Product:
        if prod.categoryName == "Monitori":
            prod.price = round(prod.price * 1.1, 2)
        return prod

    def adjust_product_description(self, prod: Product) -> Product:
        if prod.description:
            prod.description = re.sub(
                r"brzina", "performanse", prod.description, flags=re.I
            )
        return prod

    def process_product(self, product: Product) -> Product:
        product = self.adjust_product_price_for_monitors(product)
        product = self.adjust_product_description(product)
        return product

    async def fetch_products(self, jwt: str) -> list[Product]:
        try:
            res = await self.client.get(
                url=KONOVO_PRODUCTS_PATH, headers=self.auth_headers(jwt)
            )
            res.raise_for_status()
            products = TypeAdapter(list[Product]).validate_python(res.json())
            return products
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                raise AuthenticationError(
                    code="auth_token_invalid",
                    message="Not authenticated",
                    detail="Token is missing or is invalid",
                )
        except httpx.RequestError:
            raise UnavailableError(
                code="service_unavailable",
                message="External service unavailable right now",
                detail="Please try again later",
            )
        raise

    def filter_products_by_brand_ids(
        self, products: list[Product], brand_ids: list[str]
    ) -> list[Product]:
        ids = (
            [id.strip() for id in brand_ids[0].split(",") if id.strip()]
            if len(brand_ids) == 1
            else brand_ids
        )
        return [p for p in products if p.sif_productbrand and p.sif_productbrand in ids]

    def filter_products_by_category_ids(
        self, products: list[Product], category_ids: list[str]
    ) -> list[Product]:
        ids = (
            [id.strip() for id in category_ids[0].split(",") if id.strip()]
            if len(category_ids) == 1
            else category_ids
        )
        return [
            p
            for p in products
            if p.sif_productcategory and p.sif_productcategory in ids
        ]

    def filter_products_by_brand(
        self, products: list[Product], brand: str
    ) -> list[Product]:
        return [p for p in products if brand.lower() in ((p.brandName or "").lower())]

    def filter_products_by_category(
        self, products: list[Product], category: str
    ) -> list[Product]:
        return [
            p for p in products if category.lower() in ((p.categoryName or "").lower())
        ]

    def filter_products_by_name(
        self, products: list[Product], name: str
    ) -> list[Product]:
        return [p for p in products if name.lower() in p.naziv.lower()]

    def filter_products_by_price(
        self,
        products: list[Product],
        price_lt: float | None,
        price_lte: float | None,
        price_gt: float | None,
        price_gte: float | None,
    ) -> list[Product]:
        min_price = price_gte or price_gt
        max_price = price_lte or price_lt
        if min_price:
            if (price_gt and price_gte) or (price_gte):
                products = [p for p in products if p.price >= min_price]
            elif price_gt:
                products = [p for p in products if p.price > min_price]
        if max_price:
            if (price_lt and price_lte) or (price_lte):
                products = [p for p in products if p.price <= max_price]
            elif price_lt:
                products = [p for p in products if p.price < max_price]
        return products

    def sort_products(self, products: list[Product], sort: str) -> list[Product]:
        sort_by = sort.lstrip("-")
        descending = sort.startswith("-")
        if sort_by == "price":
            products.sort(key=lambda p: p.price, reverse=descending)
        return products

    def paginate_products(
        self,
        products: list[Product],
        pagination: PaginationFilters,
    ) -> PaginatedProducts:
        total = len(products)
        page = max(1, pagination.page or 1)
        page_size = max(1, pagination.page_size or total)
        start = (page - 1) * page_size
        end = start + (page_size or total)
        paginated = PaginatedProducts(
            products=products[start:end],
            meta=Pagination(page=page, page_size=page_size, total=total),
        )
        return paginated

    def filter_products(
        self,
        products: list[Product],
        filters: ProductFilters,
    ) -> list[Product]:
        if filters.category_ids:
            products = self.filter_products_by_category_ids(
                products=products, category_ids=filters.category_ids
            )
        if filters.brand_ids:
            products = self.filter_products_by_brand_ids(
                products=products, brand_ids=filters.brand_ids
            )
        if not filters.category_ids and filters.category:
            products = self.filter_products_by_category(
                products=products, category=filters.category
            )
        if not filters.brand_ids and filters.brand:
            products = self.filter_products_by_brand(
                products=products, brand=filters.brand
            )
        if filters.name:
            products = self.filter_products_by_name(
                products=products, name=filters.name
            )
        if any(
            [filters.price_lt, filters.price_lte, filters.price_gt, filters.price_gte]
        ):
            products = self.filter_products_by_price(
                products=products,
                price_lt=filters.price_lt,
                price_lte=filters.price_lte,
                price_gt=filters.price_gt,
                price_gte=filters.price_gte,
            )
        if filters.sort:
            products = self.sort_products(products=products, sort=filters.sort)
        return products

    async def list_products(
        self,
        jwt: str,
        filters: ProductFilters,
        pagination: PaginationFilters,
    ) -> PaginatedProducts:
        products = await self.fetch_products(jwt=jwt)
        filtered = self.filter_products(products, filters=filters)
        processed = [self.process_product(p) for p in filtered]
        paginated = self.paginate_products(processed, pagination)
        return paginated

    async def get_product_by_id(self, jwt: str, product_id: int) -> Product:
        products = await self.fetch_products(jwt=jwt)
        for p in products:
            if p.sif_product == str(product_id):
                return self.process_product(p)
        raise NotFoundError(
            code="product_not_found",
            message="Product no found",
            detail=f"Product with id: {product_id} does not exist",
        )
