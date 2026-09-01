import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domains.catalog.models import QuestionType


class QuestionOption(BaseModel):
    value: str = Field(min_length=1, max_length=200)
    label: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=1000)


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    key: str
    label: str
    help_text: str | None
    question_type: QuestionType
    required: bool
    options: list[QuestionOption] | None
    validation: dict[str, object] | None
    sort_order: int


class ServiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    category: str
    base_price: Decimal | None
    pricing_model: str
    duration_minutes: int | None
    is_active: bool
    is_bookable: bool


class ServiceDetail(ServiceRead):
    questions: list[QuestionRead]


class QuestionWrite(BaseModel):
    key: str = Field(pattern=r"^[a-z][a-z0-9_]{1,99}$")
    label: str = Field(min_length=1, max_length=240)
    help_text: str | None = None
    question_type: QuestionType
    required: bool = False
    options: list[QuestionOption] | None = None
    validation: dict[str, object] | None = None
    sort_order: int = 0

    @model_validator(mode="after")
    def choices_require_options(self) -> "QuestionWrite":
        if (
            self.question_type in {QuestionType.single_choice, QuestionType.multi_choice}
            and not self.options
        ):
            raise ValueError("Choice questions require options")
        return self


class ServiceWrite(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=100)
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    category: str = Field(default="home-services", min_length=1, max_length=100)
    base_price: Decimal | None = Field(default=None, ge=0)
    pricing_model: str = Field(default="quote_required", pattern="^(fixed|quote_required)$")
    duration_minutes: int = Field(ge=15, le=1440)
    is_bookable: bool = False
    sort_order: int = 0
    questions: list[QuestionWrite] = Field(default_factory=list)

    @model_validator(mode="after")
    def fixed_pricing_requires_price(self) -> "ServiceWrite":
        if self.pricing_model == "fixed" and self.base_price is None:
            raise ValueError("Fixed pricing requires base_price")
        return self
