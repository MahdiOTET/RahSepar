from typing import Literal
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    mobile: str = Field(
        min_length=10,
        max_length=15,
        pattern=r"^\+?\d+$",
    )

    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"


class CurrentUserResponse(BaseModel):
    id: int
    mobile: str
    profiles: list[str]
