import os
from pathlib import Path
import joblib
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session
from .models import ImportedInvoice, AnomalyPrediction

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ["log_total_gbp", "log_line_count", "log_total_quantity", "log_max_unit_price", "hour", "weekday", "has_customer"]

def project1_root() -> Path:
    return Path(os.getenv("PROJECT1_ROOT", str(ROOT.parent / "dataset"))).resolve()

def import_project1(db: Session, source: Path | None = None) -> dict:
    source = source or project1_root() / "data/processed/invoice_predictions.parquet"
    if not source.is_file():
        raise FileNotFoundError(f"Project 1 predictions missing: {source}")
    frame = pd.read_parquet(source)
    needed = {"InvoiceNo", "invoice_date", "country", "total_gbp", "line_count", "anomaly_score", "is_anomaly", "subset", "rule_flag"}
    if not needed.issubset(frame.columns):
        raise ValueError(f"Missing Project 1 columns: {sorted(needed - set(frame.columns))}")
    if frame.InvoiceNo.isna().any() or frame.InvoiceNo.duplicated().any():
        raise ValueError("Source invoice identifiers must be unique and non-null")
    ids = set(db.scalars(select(ImportedInvoice.invoice_id)).all())
    added = 0
    for row in frame.itertuples(index=False):
        invoice_id = str(row.InvoiceNo)
        if invoice_id in ids:
            continue
        invoice = ImportedInvoice(invoice_id=invoice_id, invoice_date=row.invoice_date.to_pydatetime(), country=str(row.country) if pd.notna(row.country) else None, total_gbp=float(row.total_gbp), line_count=int(row.line_count))
        invoice.prediction = AnomalyPrediction(anomaly_score=float(row.anomaly_score), is_anomaly=bool(row.is_anomaly), subset=str(row.subset), rule_flag=bool(row.rule_flag))
        db.add(invoice)
        added += 1
    db.commit()
    return {"source_rows": len(frame), "imported": added, "already_present": len(frame) - added}

def predict(features: dict, model_path: Path | None = None) -> dict:
    model_path = model_path or project1_root() / "models/isolation_forest.joblib"
    if not model_path.is_file():
        raise FileNotFoundError("Project 1 model artifact is unavailable")
    artifact = joblib.load(model_path)  # Configured local, trusted Project 1 artifact only.
    if artifact.get("features") != FEATURES:
        raise ValueError("Saved model features differ from the documented input schema")
    frame = pd.DataFrame([features], columns=FEATURES)
    pipeline = artifact["pipeline"]
    return {"anomaly_score": float(-pipeline.decision_function(frame)[0]), "is_anomaly": bool(pipeline.predict(frame)[0] == -1), "interpretation": "Statistical anomaly flagged for manual review" if pipeline.predict(frame)[0] == -1 else "Not flagged by the statistical anomaly model"}
