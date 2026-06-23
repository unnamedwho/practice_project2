from contextlib import asynccontextmanager
from datetime import date
from decimal import Decimal
from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import Document, ImportedInvoice, AnomalyPrediction
from .schemas import DocumentCreate, DocumentPatch, DocumentOut, DocumentType, Status, FeaturePayload
from .services import import_project1, predict

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Accounting Document API", description="Educational prototype for simulated accounting documents and Project 1 retail invoice anomaly results. Not an official accounting integration or fraud detector.", version="1.0.0", lifespan=lifespan)

@app.get("/health", tags=["Health"], summary="Check application and database")
def health(db: Session = Depends(get_db)):
    db.execute(select(1))
    return {"status": "ok", "database": "ok"}

@app.post("/api/v1/documents", response_model=DocumentOut, status_code=201, tags=["Documents"], summary="Create a simulated accounting document")
def create_document(data: DocumentCreate, db: Session = Depends(get_db)):
    doc = Document(**data.model_dump(mode="python"))
    db.add(doc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Document number already exists")
    db.refresh(doc)
    return doc

@app.get("/api/v1/documents", tags=["Documents"], summary="List and filter documents")
def list_documents(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), document_type: DocumentType | None = None, status: Status | None = None, date_from: date | None = None, date_to: date | None = None, counterparty: str | None = None, min_amount: Decimal | None = Query(None, ge=0), max_amount: Decimal | None = Query(None, ge=0), db: Session = Depends(get_db)):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "date_from must not exceed date_to")
    if min_amount is not None and max_amount is not None and min_amount > max_amount:
        raise HTTPException(422, "min_amount must not exceed max_amount")
    query = select(Document)
    if document_type: query = query.where(Document.document_type == document_type.value)
    if status: query = query.where(Document.status == status.value)
    if date_from: query = query.where(Document.issue_date >= date_from)
    if date_to: query = query.where(Document.issue_date <= date_to)
    if counterparty: query = query.where(Document.counterparty_name.ilike(f"%{counterparty}%"))
    if min_amount is not None: query = query.where(Document.amount_cents >= int(min_amount * 100))
    if max_amount is not None: query = query.where(Document.amount_cents <= int(max_amount * 100))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(Document.id).offset((page - 1) * page_size).limit(page_size)).all()
    return {"items": [DocumentOut.model_validate(x) for x in rows], "total": total, "page": page, "page_size": page_size}

@app.get("/api/v1/documents/{document_id}", response_model=DocumentOut, tags=["Documents"], summary="Get a document")
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc: raise HTTPException(404, "Document not found")
    return doc

@app.patch("/api/v1/documents/{document_id}", response_model=DocumentOut, tags=["Documents"], summary="Update a document")
def patch_document(document_id: int, data: DocumentPatch, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc: raise HTTPException(404, "Document not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(doc, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Document number already exists")
    db.refresh(doc)
    return doc

@app.delete("/api/v1/documents/{document_id}", status_code=204, tags=["Documents"], summary="Delete a test document")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.get(Document, document_id)
    if not doc: raise HTTPException(404, "Document not found")
    db.delete(doc)
    db.commit()
    return Response(status_code=204)

@app.get("/api/v1/statistics", tags=["Statistics"], summary="Summarize simulated documents")
def statistics(db: Session = Depends(get_db)):
    by_type = dict(db.execute(select(Document.document_type, func.count()).group_by(Document.document_type)).all())
    by_status = dict(db.execute(select(Document.status, func.count()).group_by(Document.status)).all())
    # Sum exact integer minor units; never use a binary float for document money.
    by_currency = {}
    for currency, cents in db.execute(select(Document.currency, Document.amount_cents)):
        by_currency[currency] = by_currency.get(currency, 0) + cents
    return {"total_documents": db.scalar(select(func.count()).select_from(Document)), "by_type": by_type, "by_status": by_status, "amount_by_currency": {k: str(Decimal(v) / Decimal(100)) for k, v in by_currency.items()}, "documents_linked_to_anomaly_predictions": 0, "imported_invoices": db.scalar(select(func.count()).select_from(ImportedInvoice)), "anomaly_predictions": db.scalar(select(func.count()).select_from(AnomalyPrediction))}

@app.post("/api/v1/import/project1", tags=["Project 1 import"], summary="Import configured Project 1 invoice predictions")
def import_predictions(db: Session = Depends(get_db)):
    try: return import_project1(db)
    except FileNotFoundError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(422, str(exc))

@app.get("/api/v1/anomalies", tags=["Anomalies"], summary="List imported anomaly predictions")
def list_anomalies(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), flagged_only: bool = False, db: Session = Depends(get_db)):
    query = select(AnomalyPrediction, ImportedInvoice).join(ImportedInvoice)
    if flagged_only: query = query.where(AnomalyPrediction.is_anomaly.is_(True))
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(AnomalyPrediction.invoice_id).offset((page - 1) * page_size).limit(page_size))
    return {"items": [{"invoice_id": p.invoice_id, "invoice_date": i.invoice_date, "country": i.country, "total_gbp": i.total_gbp, "line_count": i.line_count, "anomaly_score": p.anomaly_score, "is_anomaly": p.is_anomaly, "subset": p.subset, "rule_flag": p.rule_flag} for p, i in rows], "total": total, "page": page, "page_size": page_size}

@app.post("/api/v1/anomalies/predict", tags=["Anomalies"], summary="Score one compatible invoice feature vector")
def predict_anomaly(data: FeaturePayload):
    try: return predict(data.model_dump())
    except FileNotFoundError as exc: raise HTTPException(503, str(exc))
    except ValueError as exc: raise HTTPException(503, str(exc))

@app.get("/api/v1/anomalies/{invoice_id}", tags=["Anomalies"], summary="Get an imported invoice prediction")
def get_anomaly(invoice_id: str, db: Session = Depends(get_db)):
    p = db.get(AnomalyPrediction, invoice_id)
    if not p: raise HTTPException(404, "Imported invoice prediction not found")
    return {"invoice_id": p.invoice_id, "anomaly_score": p.anomaly_score, "is_anomaly": p.is_anomaly, "subset": p.subset, "rule_flag": p.rule_flag}
