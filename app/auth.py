from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from app.errors import AuthorizationError


class AuthorizationBearer(HTTPBearer):
    async def __call__(self, request: Request) -> HTTPAuthorizationCredentials | None:
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if not (authorization and scheme and credentials):
            if self.auto_error:
                raise AuthorizationError(
                    code="invalid_auth_token",
                    message="Not authenticated",
                    detail="Missing or invalid auth token",
                )
            else:
                return None
        if scheme.lower() != "bearer":
            if self.auto_error:
                raise AuthorizationError(
                    code="invalid_auth_token",
                    message="Not authenticated",
                    detail="Invalid authorization scheme, expected Bearer <token>",
                )
            else:
                return None
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
