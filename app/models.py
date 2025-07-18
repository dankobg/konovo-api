from pydantic import BaseModel


class KonovoApiError(BaseModel):
    code: str
    message: str
    detail: str


class ValidationErrorDetail(BaseModel):
    loc: list[str | int]
    msg: str
    type: str


class KonovoValidationError(BaseModel):
    code: str
    message: str
    detail: list[ValidationErrorDetail]


class Pagination(BaseModel):
    total: int
    page: int
    page_size: int


class PaginationFilters(BaseModel):
    page: int | None
    page_size: int | None


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    token: str


class Product(BaseModel):
    naziv: str
    sku: str
    ean: str | None
    price: float
    vat: str
    stock: str
    description: str | None
    imgsrc: str
    sif_productcategory: str | None
    sif_productbrand: str | None
    sif_product: str
    categoryName: str | None
    brandName: str | None


class PaginatedProducts(BaseModel):
    products: list[Product]
    meta: Pagination


class ProductFilters(BaseModel):
    name: str | None
    brand_ids: list[str] | None
    category_ids: list[str] | None
    brand: str | None
    category: str | None
    price_lt: float | None
    price_lte: float | None
    price_gt: float | None
    price_gte: float | None
    sort: str | None
    # ofc price could be its own separate filter model, that is reusable...
