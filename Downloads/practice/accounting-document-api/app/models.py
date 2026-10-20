from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, BigInteger, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

def utcnow():
    return datetime.now(timezone.utc)

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_number: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    document_type: Mapped[str] = mapped_column(String(20), index=True)
    issue_date: Mapped[date] = mapped_column(Date, index=True)
    counterparty_name: Mapped[str] = mapped_column(String(200), index=True)
    amount_cents: Mapped[int] = mapped_column("amount", BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(20), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    @property
    def amount(self) -> Decimal:
        return Decimal(self.amount_cents) / Decimal(100)

    @amount.setter
    def amount(self, value: Decimal) -> None:
        self.amount_cents = int(value * 100)

class ImportedInvoice(Base):
    __tablename__ = "imported_invoices"
    invoice_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    invoice_date: Mapped[datetime] = mapped_column(DateTime)
    country: Mapped[str | None] = mapped_column(String(100))
    total_gbp: Mapped[float] = mapped_column(Float)
    line_count: Mapped[int] = mapped_column(Integer)
    prediction: Mapped["AnomalyPrediction"] = relationship(back_populates="invoice", uselist=False, cascade="all, delete-orphan")

class AnomalyPrediction(Base):
    __tablename__ = "anomaly_predictions"
    invoice_id: Mapped[str] = mapped_column(ForeignKey("imported_invoices.invoice_id", ondelete="CASCADE"), primary_key=True)
    anomaly_score: Mapped[float] = mapped_column(Float)
    is_anomaly: Mapped[bool] = mapped_column(Boolean)
    subset: Mapped[str] = mapped_column(String(20))
    rule_flag: Mapped[bool] = mapped_column(Boolean)
    invoice: Mapped[ImportedInvoice] = relationship(back_populates="prediction")
