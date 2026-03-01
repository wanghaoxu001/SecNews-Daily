from fastapi import APIRouter, HTTPException, status

from app.config import settings
from app.schemas.auth import LoginRequest, TokenResponse
from app.auth import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest):
    if body.username != settings.ADMIN_USERNAME or body.password != settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = create_access_token(body.username)
    return TokenResponse(access_token=token)
