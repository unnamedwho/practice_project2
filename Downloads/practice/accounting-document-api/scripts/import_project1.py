"""Import the configured local Project 1 prediction artifact."""
from app.database import Base, engine, SessionLocal
from app.services import import_project1

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        print(import_project1(db))
