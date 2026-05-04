import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DB_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def reset_db():
    yield
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


@pytest.fixture
def buyer(client):
    client.post("/auth/register", json={
        "email": "buyer@test.com", "username": "testbuyer",
        "password": "password123", "role": "buyer",
    })
    r = client.post("/auth/login", json={"email": "buyer@test.com", "password": "password123"})
    return r.json()["access_token"]


@pytest.fixture
def seller(client):
    client.post("/auth/register", json={
        "email": "seller@test.com", "username": "testseller",
        "password": "password123", "role": "seller",
    })
    r = client.post("/auth/login", json={"email": "seller@test.com", "password": "password123"})
    return r.json()["access_token"]
