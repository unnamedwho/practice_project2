# Technical Report: Accounting Document API

## 1. Introduction

This independent educational project connects a simulated accounting document API with the results of an earlier financial transaction analysis project. The source company context is inspiration only; this software is not an ARQA BUH product or a real IS ESF integration.

## 2. Business problem

Teams handling many documents need reliable search, status tracking, and a way to review unusual records. Retail transaction anomaly predictions can demonstrate that workflow, but cannot establish fraud or legal invoice validity.

## 3. Objective

Implement a working FastAPI backend for test documents, import Project 1's retail invoice predictions without changing that project, and expose the saved model for complete compatible invoice feature vectors.

## 4. Technology stack

Python 3.14.7, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite, pandas, pyarrow, scikit-learn, joblib, pytest, and HTTPX. PostgreSQL is configurable through `DATABASE_URL` and `psycopg`, but was not tested against a server.

## 5. Architecture

The FastAPI app validates requests and calls SQLAlchemy sessions. Three distinct tables keep simulated documents, UCI Online Retail invoices, and model predictions apart. A configured import service reads the existing Project 1 Parquet file. The inference service loads the existing trusted local joblib pipeline and checks its feature list before scoring. Swagger UI is generated at `/docs`.

## 6. Database design

`documents` has a unique document number, type, date, counterparty, currency, status, description, and timestamps. Document amounts are stored as **integer minor units** (cents/tiyn) in the database and exposed as Decimal values. This avoids binary floating point arithmetic for authoritative simulated amounts. `imported_invoices` preserves the Project 1 invoice identifier, timestamp, country, source `total_gbp`, and line count. `anomaly_predictions` has a one-to-one foreign key to imported invoices and stores score, model flag, train/holdout subset, and comparison rule flag. The retail amount remains an ML source value and is never combined with simulated accounting totals.

## 7. REST API

Document routes implement create, list, retrieve, patch, and delete. Filtering is performed in SQL with type, status, date range, counterparty substring, amount bounds, and pagination. Statistics group document counts by type and status, accumulate exact document minor units by currency, and report imported row counts. Invalid payloads receive 422, missing rows 404, duplicate numbers 409, and unavailable local artifacts 503.

## 8. Project 1 integration

Inspection found `data/processed/invoice_predictions.parquet` with 20,725 rows, `models/isolation_forest.joblib`, the feature definitions in `src/feature_engineering.py`, and the source SQL schema. Import preserves invoice IDs and predictions in separate tables. The import checks required columns and uniqueness, inserts only missing IDs, and is idempotent. The Project 1 directory was not modified.

## 9. ML inference workflow

The saved artifact has a scikit-learn pipeline and seven ordered features: `log_total_gbp`, `log_line_count`, `log_total_quantity`, `log_max_unit_price`, `hour`, `weekday`, and `has_customer`. Project 1 computes these from complete sale invoices. The API accepts exactly those seven values and calls the saved pipeline's `decision_function` and `predict`; anomaly score is the negative decision value, so higher means more unusual. A standalone document amount does not provide enough information. The response says whether the model flagged a statistical anomaly for manual review, never confirmed fraud.

## 10. Testing and verified behavior

The isolated pytest suite passed **2 tests** covering create, validation errors, duplicate document numbers, retrieval, patch, delete, SQL filters, pagination, statistics, persistence, the full 20,725-row import, repeated import with zero duplicates, stored prediction retrieval, compatible inference, invalid inference input, and missing artifacts. The first complete run took 70.98 seconds; the final run after the amount storage change passed in 2.29 seconds. A live Uvicorn server returned HTTP 200 for `/health` and `/docs`. Live `/api/v1/statistics` returned 3 seeded fictional documents, KZT 214251.25, 20,725 imported invoices, and 20,725 predictions. Live retrieval of invoice `536365` returned score `-0.17485654282273855` and `is_anomaly=false`. A live inference request with that invoice's seven saved feature values reproduced the same score and flag. The real Project 2 database import reported `source_rows=20725`, `imported=20725`, `already_present=0`; a second import reported `imported=0`, `already_present=20725`. Live CRUD verified creation, an exact 0.29 amount filter and total, update, and deletion of a temporary fictional document.

## 11. Limitations

The document model is simplified and has no legal or tax validity. There is no authentication, role control, audit trail, migrations, external accounting system integration, or exchange-rate conversion. Import assumes a trusted local Project 1 artifact and can take around a minute. The existing model reflects historical UK retail invoices and may be unsuitable for other businesses or modern accounting documents. PostgreSQL support is configured but unverified.

## 12. Future improvements

Add database migrations, authorization, audit events, a background import job, stronger model monitoring, a reviewed anomaly feedback workflow, and an integration contract for a real document source when legally and technically appropriate.
