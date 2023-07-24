from typing import Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber


M = TypeVar("M")


class PaginatedResponse(BaseModel, Generic[M]):
    count: int = Field(description="Number of items returned in the response")
    items: List[M] = Field(
        description="List of items returned in the response following given criteria"
    )


class ContactSchema(BaseModel):
    name: str = Field(title="The name of person", max_length=255)
    surname: str | None = Field(title="The surname of person", max_length=255)
    phone: PhoneNumber = Field(
        title="Phone number",
        examples=["+48123456789"],
    )
    email: EmailStr | None = Field(
        title="Email",
        examples=["name@site.com"],
    )


class ContactDB(ContactSchema):
    id: int

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True


class WelcomeMsgSchema(BaseModel):
    msg: str
