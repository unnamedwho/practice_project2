# Accounting Document API

An independent educational FastAPI prototype for simulated accounting documents. It imports UCI Online Retail invoice predictions from [Project 1](../dataset/README.md) as separate retail records and uses Project 1's saved Isolation Forest to score compatible feature vectors. It is not an official ARQA BUH component, a Kazakhstan electronic invoice integration, or a production accounting system. Statistical anomalies are candidates for manual review, not confirmed fraud.

## Features and architecture

- FastAPI and Pydantic v2 validate document and model requests.
- SQLAlchemy 2.x stores simulated documents, imported retail invoices, and linked predictions in distinct tables.
- SQLite is the default; `DATABASE_URL` may point to PostgreSQL with `psycopg` (PostgreSQL has not been tested here).
- The local, configured Project 1 Parquet and joblib artifacts are read without modifying Project 1. Import is idempotent.
- Monetary totals for simulated documents are kept separately by currency. Retail `total_gbp` is a Project 1 ML data field; it is not treated as a legal accounting amount or converted to KZT.

## Requirements and setup

Python 3.11+ with compatible packages. This project was executed with Python 3.14.7. From this directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Default paths assume this project and Project 1's `dataset/` directory are siblings. Copy `.env.example` values into your shell environment if you need other paths. The app reads `DATABASE_URL` and `PROJECT1_ROOT` directly; it does not auto-load `.env` files. Example:

```bash
export DATABASE_URL='sqlite:///./accounting.db'
export PROJECT1_ROOT='../dataset'
```

Run from this directory:

```bash
.venv/bin/python -m scripts.seed
.venv/bin/python -m scripts.import_project1
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The seed is optional and idempotent. It adds three entirely fictional KZT documents. The importer is also available as `POST /api/v1/import/project1`. It reads only the configured local artifact and accepts no request path. The server creates database tables at startup. Open [Swagger UI](http://127.0.0.1:8000/docs) when running.

## Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Application and database check |
| `POST /api/v1/documents` | Create a simulated document |
| `GET /api/v1/documents` | Paginate and filter by type, status, date, counterparty, and amount |
| `GET /api/v1/documents/{document_id}` | Retrieve one document |
| `PATCH /api/v1/documents/{document_id}` | Update provided fields |
| `DELETE /api/v1/documents/{document_id}` | Delete a test document |
| `GET /api/v1/statistics` | Document counts, currency totals, import counts |
| `POST /api/v1/import/project1` | Idempotent Project 1 import |
| `GET /api/v1/anomalies` | Paginated stored predictions; `flagged_only=true` supported |
| `GET /api/v1/anomalies/{invoice_id}` | Stored score and flag for an invoice |
| `POST /api/v1/anomalies/predict` | Score a complete seven-feature invoice vector |

## Example requests

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents -H 'Content-Type: application/json' -d '{"document_number":"INV-TEST-01","document_type":"invoice","issue_date":"2026-10-20","counterparty_name":"Fictional Partner","amount":"125000.50","currency":"KZT","status":"draft"}'
curl 'http://127.0.0.1:8000/api/v1/documents?status=draft&min_amount=1000&page=1&page_size=20'
curl http://127.0.0.1:8000/api/v1/anomalies/536365
curl -X POST http://127.0.0.1:8000/api/v1/anomalies/predict -H 'Content-Type: application/json' -d '{"log_total_gbp":4.942499211124802,"log_line_count":2.0794415416798357,"log_total_quantity":3.713572066704308,"log_max_unit_price":2.157559394836426,"hour":8,"weekday":2,"has_customer":1}'
```

The seven fields above come directly from Project 1's feature engineering. The API requires all seven and forbids extras. Values should be computed from a complete, compatible invoice snapshot using Project 1's transformations. A standalone accounting document amount cannot be scored meaningfully. Missing model or import artifacts return HTTP 503; invalid feature payloads return HTTP 422.

## Tests

```bash
.venv/bin/python -m pytest -q tests
```

Tests use temporary SQLite databases and only read Project 1 artifacts. They do not alter Project 1 or the default application database.

## Limitations

No authentication, access controls, migration framework, legal invoice schema, exchange conversion, or live accounting integration. The model is an unsupervised Isolation Forest trained on historical UK retail invoices, so its score is not evidence of fraud. The import is a local bulk operation and can take about a minute on this machine. PostgreSQL configuration is implemented but has not been verified against a running server.
