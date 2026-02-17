from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=2, max_length=64)
    country: str = Field(default="Unknown", max_length=64)


class LoginRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=64)
    country: str = Field(min_length=2, max_length=64)
    avatar_url: str = Field(default="", max_length=256)


class JoinTableRequest(BaseModel):
    table_id: int
    buyin: int


class ActionRequest(BaseModel):
    action: Literal["pack", "see", "call", "raise", "show"]
    amount: int = 0


class AddBotsRequest(BaseModel):
    table_id: int
    count: int = Field(ge=1, le=5)


class TwentyNineCreateTableRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)


class TwentyNineBidRequest(BaseModel):
    amount: int = Field(ge=16, le=29)
    trump_suit: Literal["S", "H", "D", "C"]


class TwentyNinePlayRequest(BaseModel):
    card: str = Field(min_length=2, max_length=3)


class TwentyNineAddBotsRequest(BaseModel):
    count: int = Field(ge=1, le=4)
