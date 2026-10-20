from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db, make_engine
from app.main import app
from app.services import import_project1

ROOT = Path(__file__).resolve().parents[2] / "dataset"
SAMPLE = {"document_number": "T-001", "document_type": "invoice", "issue_date": "2026-10-20", "counterparty_name": "Fictional Partner", "amount": "100.25", "currency": "KZT", "status": "draft"}
FEATURES = {"log_total_gbp": 4.942499211124802, "log_line_count": 2.0794415416798357, "log_total_quantity": 3.713572066704308, "log_max_unit_price": 2.157559394836426, "hour": 8, "weekday": 2, "has_customer": 1}

@pytest.fixture
def client(tmp_path):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.sqlite'}")
    Base.metadata.create_all(engine)
    maker = sessionmaker(engine)
    def dependency():
        with maker() as db:
            yield db
    app.dependency_overrides[get_db] = dependency
    yield TestClient(app), maker
    app.dependency_overrides.clear()
    engine.dispose()

def test_crud_filter_pagination_stats_persistence(client):
    api, maker = client
    created = api.post("/api/v1/documents", json=SAMPLE)
    assert created.status_code == 201, created.text
    ident = created.json()["id"]
    assert api.post("/api/v1/documents", json=SAMPLE).status_code == 409
    for override in ({"amount": "-1"}, {"currency": "gbp"}, {"status": "unknown"}, {"document_number": " "}):
        assert api.post("/api/v1/documents", json=SAMPLE | override).status_code == 422
    assert api.get(f"/api/v1/documents/{ident}").json()["amount"] == "100.25"
    assert api.post("/api/v1/documents", json=SAMPLE | {"document_number": "T-002", "document_type": "receipt", "amount": "50.00"}).status_code == 201
    assert api.get("/api/v1/documents", params={"document_type": "invoice", "min_amount": "100", "counterparty": "Partner"}).json()["total"] == 1
    assert len(api.get("/api/v1/documents", params={"page_size": 1, "page": 2}).json()["items"]) == 1
    assert api.get("/api/v1/documents", params={"date_from": "2027-01-01", "date_to": "2026-01-01"}).status_code == 422
    assert api.patch(f"/api/v1/documents/{ident}", json={"status": "confirmed"}).json()["status"] == "confirmed"
    assert api.patch(f"/api/v1/documents/{ident}", json={"amount": None}).status_code == 422
    stats = api.get("/api/v1/statistics").json()
    assert stats["total_documents"] == 2
    assert stats["amount_by_currency"] == {"KZT": "150.25"}
    with maker() as db:
        from app.models import Document
        assert db.get(Document, ident).status == "confirmed"
    assert api.delete(f"/api/v1/documents/{ident}").status_code == 204
    assert api.get(f"/api/v1/documents/{ident}").status_code == 404

def test_import_and_inference(client, monkeypatch):
    api, maker = client
    monkeypatch.setenv("PROJECT1_ROOT", str(ROOT))
    first = api.post("/api/v1/import/project1")
    assert first.status_code == 200, first.text
    assert first.json()["imported"] == 20725
    second = api.post("/api/v1/import/project1")
    assert second.json()["imported"] == 0
    assert second.json()["already_present"] == 20725
    assert api.get("/api/v1/anomalies").json()["total"] == 20725
    assert "anomaly_score" in api.get("/api/v1/anomalies/536365").json()
    assert api.get("/api/v1/statistics").json()["imported_invoices"] == 20725
    prediction = api.post("/api/v1/anomalies/predict", json=FEATURES)
    assert prediction.status_code == 200, prediction.text
    assert prediction.json()["is_anomaly"] is False
    assert api.post("/api/v1/anomalies/predict", json={"log_total_gbp": 1}).status_code == 422
    assert api.post("/api/v1/anomalies/predict", json=FEATURES | {"extra": 1}).status_code == 422
    monkeypatch.setenv("PROJECT1_ROOT", "/missing/project1")
    assert api.post("/api/v1/anomalies/predict", json=FEATURES).status_code == 503
    assert api.post("/api/v1/import/project1").status_code == 503
    assert api.get("/api/v1/documents").status_code == 200
