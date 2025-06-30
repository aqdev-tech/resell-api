import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
from urllib.parse import urlparse, urlunparse
import subprocess

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app, get_db, Base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
parsed_url = urlparse(DATABASE_URL)
test_db_path = parsed_url.path + "_test"
TEST_DATABASE_URL = urlunparse(
    (parsed_url.scheme, parsed_url.netloc, test_db_path, parsed_url.params, parsed_url.query, parsed_url.fragment)
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Ensure the test database is created and up-to-date
    subprocess.run(["python", "create_admin.py"], check=True)
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_admin_login():
    response = client.post(
        "/admin/login",
        data={"username": "hikmaadmin", "password": "alhikmatech"},
    )
    assert response.status_code == 200
    json_response = response.json()
    assert "access_token" in json_response
    assert json_response["token_type"] == "bearer"

def test_admin_dashboard_access():
    # Log in to get a token
    response = client.post(
        "/admin/login",
        data={"username": "hikmaadmin", "password": "alhikmatech"},
    )
    token = response.json()["access_token"]

    # Access the dashboard with the token
    response = client.get(
        "/admin/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    dashboard_data = response.json()
    assert "pending_listings" in dashboard_data
    assert "active_listings" in dashboard_data
    assert "sold_listings" in dashboard_data
