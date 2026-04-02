from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    contact_info: str
    is_active: bool
    is_admin: bool


class SignInRequest(BaseModel):
    email: EmailStr
    otp: str


class LoginStartRequest(BaseModel):
    email: EmailStr


class LoginStartResponse(BaseModel):
    pass


class SignInResponse(BaseModel):
    jwt: str


class UserWithJwtResponse(BaseModel):
    user: UserView
    jwt: str


class NotificationsWithJwtResponse(BaseModel):
    notifications: list["NotificationView"]
    jwt: str


class NotificationWithJwtResponse(BaseModel):
    notification: "NotificationView"
    jwt: str


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    contact_info: str | None = None
    is_active: bool | None = None


class NotificationView(BaseModel):
    id: str
    user_id: str
    partner_user_id: str
    partner_email: EmailStr
    partner_full_name: str
    status: Literal["MET", "UNMET"]
    week_key: str
    created_at: str


class TriggerPairingResponse(BaseModel):
    pairs_created: int
    notifications_created: int
    jwt: str
