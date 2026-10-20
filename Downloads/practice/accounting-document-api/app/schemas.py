from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

class DocumentType(str, Enum):
    invoice = "invoice"
    act = "act"
    receipt = "receipt"

class Status(str, Enum):
    draft = "draft"
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"

Money = Annotated[Decimal, Field(max_digits=18, decimal_places=2, ge=0, le=Decimal("9999999999999999.99"))]
Currency = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]

class DocumentCreate(BaseModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{"document_number": "INV-2026-001", "document_type": "invoice", "issue_date": "2026-10-20", "counterparty_name": "Fictional Steppe Supplies", "amount": "125000.50", "currency": "KZT", "status": "draft", "description": "Training example"}]})
    document_number: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    document_type: DocumentType
    issue_date: date
    counterparty_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    amount: Money
    currency: Currency = "KZT"
    status: Status = Status.draft
    description: str | None = None

class DocumentPatch(BaseModel):
    document_number: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)] | None = None
    document_type: DocumentType | None = None
    issue_date: date | None = None
    counterparty_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)] | None = None
    amount: Money | None = None
    currency: Currency | None = None
    status: Status | None = None
    description: str | None = None

    @model_validator(mode="after")
    def no_null_required(self):
        required = {"document_number", "document_type", "issue_date", "counterparty_name", "amount", "currency", "status"}
        if any(getattr(self, key) is None for key in required & self.model_fields_set):
            raise ValueError("Required document fields cannot be null")
        return self

class DocumentOut(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

class FeaturePayload(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"log_total_gbp": 4.942499211124802, "log_line_count": 2.0794415416798357, "log_total_quantity": 3.713572066704308, "log_max_unit_price": 2.157559394836426, "hour": 8, "weekday": 2, "has_customer": 1}]})
    log_total_gbp: float = Field(ge=0, allow_inf_nan=False)
    log_line_count: float = Field(ge=0, allow_inf_nan=False)
    log_total_quantity: float = Field(ge=0, allow_inf_nan=False)
    log_max_unit_price: float = Field(ge=0, allow_inf_nan=False)
    hour: int = Field(ge=0, le=23)
    weekday: int = Field(ge=0, le=6)
    has_customer: int = Field(ge=0, le=1)
