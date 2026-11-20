import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app import models  # noqa: F401  (φορτώνει όλα τα models στο Base)
from app.database import Base, get_db
from app.main import app
from app.models import User
from app.models.enums import Role

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://flowdesk:flowdesk@localhost:5432/flowdesk_test",
)
PASSWORD = "secret123"

engine = create_engine(TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(client, db):
    def _make_user(email: str, role: Role = Role.EMPLOYEE) -> dict:
        client.post(
            "/auth/register",
            json={"email": email, "full_name": "Test User", "password": PASSWORD},
        )
        if role != Role.EMPLOYEE:
            user = db.scalar(select(User).where(User.email == email))
            user.role = role
            db.commit()
        response = client.post("/auth/login", data={"username": email, "password": PASSWORD})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make_user


@pytest.fixture
def users(make_user):
    return {
        "admin": make_user("admin@test.dev", Role.ADMIN),
        "employee": make_user("employee@test.dev"),
        "finance": make_user("finance@test.dev", Role.FINANCE),
        "manager": make_user("manager@test.dev", Role.MANAGER),
        "manager2": make_user("manager2@test.dev", Role.MANAGER),
    }


@pytest.fixture
def workflow(client, users):
    response = client.post(
        "/workflows",
        headers=users["admin"],
        json={
            "name": "Expense",
            "steps": [
                {"name": "Finance check", "approver_role": "finance"},
                {"name": "Manager approval", "approver_role": "manager"},
                {"name": "Final approval", "approver_role": "admin"},
            ],
        },
    )
    return response.json()