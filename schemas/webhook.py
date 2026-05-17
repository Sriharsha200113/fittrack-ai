from pydantic import BaseModel


class WhatsAppWebhook(BaseModel):
    phone: str
    group_id: str
    message: str
    sender_name: str
    image_data: str | None = None
    image_mimetype: str | None = None


class DMWebhook(BaseModel):
    phone: str
    message: str
    sender_name: str
    image_data: str | None = None
    image_mimetype: str | None = None


class GroupJoinWebhook(BaseModel):
    group_id: str
    member_phones: list[str]


class WebhookResponse(BaseModel):
    reply: str


class GroupJoinResponse(BaseModel):
    reply: str
    dm_invites: list[dict]
