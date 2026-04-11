from pydantic import BaseModel, ConfigDict, EmailStr


class ProfileView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    contact_info: str
    about_me: str
    interests: list[int]

class SignInRequest(BaseModel):
    email: EmailStr
    otp: str


class LoginStartRequest(BaseModel):
    email: EmailStr


class LoginStartResponse(BaseModel):
    pass


class SignInResponse(BaseModel):
    jwt: str


class NotificationResponse(BaseModel):
    notification: "NotificationView"


class EmptyResponse(BaseModel):
    pass


class UserUpdateRequest(BaseModel):
    name: str | None = None
    contact_info: str | None = None
    about_me: str | None = None
    is_active: bool | None = None
    interests: list[int] | None = None


class NotificationView(BaseModel):
    id: str
    user_id: str
    partner_user_id: str
    partner_name: str
    met: bool
    week_key: str
    created_at: str


class ConfirmRequest(BaseModel):
    notification_id: str
