from pydantic import BaseModel, ConfigDict, EmailStr


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    full_name: str
    contact_info: str
    is_active: bool


class SignInRequest(BaseModel):
    email: EmailStr
    otp: str


class LoginStartRequest(BaseModel):
    email: EmailStr


class LoginStartResponse(BaseModel):
    pass


class SignInResponse(BaseModel):
    jwt: str


class UserResponse(BaseModel):
    user: UserView


class NotificationsResponse(BaseModel):
    notifications: list["NotificationView"]


class NotificationResponse(BaseModel):
    notification: "NotificationView"


class EmptyResponse(BaseModel):
    pass


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
    met: bool
    week_key: str
    created_at: str


class ConfirmRequest(BaseModel):
    notification_id: str
