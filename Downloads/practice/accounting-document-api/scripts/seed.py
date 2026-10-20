"""Seed entirely fictional training documents; safe to run repeatedly."""
from datetime import date
from decimal import Decimal
from sqlalchemy import select
from app.database import Base, engine, SessionLocal
from app.models import Document

SAMPLES = [
    ("DEMO-INV-001", "invoice", "Fictional Steppe Supplies", "125000.50"),
    ("DEMO-ACT-001", "act", "Imaginary Meridian Services", "85000.00"),
    ("DEMO-REC-001", "receipt", "Sample City Stationery", "4250.75"),
]

def main():
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        for number, kind, partner, amount in SAMPLES:
            if db.scalar(select(Document.id).where(Document.document_number == number)) is None:
                db.add(Document(document_number=number, document_type=kind, issue_date=date(2026, 10, 20), counterparty_name=partner, amount=Decimal(amount), currency="KZT", status="draft", description="Fictional educational demonstration"))
        db.commit()
    print("Seed complete")

if __name__ == "__main__":
    main()
