import os
import subprocess
import sys
import threading
import uuid
from http.server import ThreadingHTTPServer

import psycopg
import pytest
from fastapi.testclient import TestClient
from provider_stub import OpenAIHandler
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from cinemood.app import create_app


@pytest.fixture(scope="session")
def provider_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), OpenAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}/v1"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def database_url(monkeypatch, provider_url):
    admin = os.environ["TEST_DATABASE_URL"]
    database = "cinemood_test_" + uuid.uuid4().hex
    with psycopg.connect(admin, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    params = conninfo_to_dict(admin)
    params["dbname"] = database
    dsn = make_conninfo(**params)
    monkeypatch.setenv("DATABASE_URL", dsn)
    monkeypatch.setenv("OPENAI_API_KEY", "test-only")
    monkeypatch.setenv("OPENAI_BASE_URL", provider_url)
    try:
        result = command("migrate")
        assert result.returncode == 0, result.stderr
        yield dsn
    finally:
        with psycopg.connect(admin, autocommit=True) as conn:
            conn.execute(
                sql.SQL("DROP DATABASE {} WITH (FORCE)").format(
                    sql.Identifier(database)
                )
            )


def command(*args):
    return subprocess.run(
        [sys.executable, "-m", "cinemood", *args],
        capture_output=True,
        text=True,
        timeout=45,
    )


@pytest.fixture
def client(database_url):
    with TestClient(create_app()) as client:
        yield client


@pytest.fixture
def loaded_client(client):
    result = command("load-fixtures")
    assert result.returncode == 0, result.stderr
    return client


@pytest.fixture
def extraction(monkeypatch):
    responses = {}
    monkeypatch.setattr(OpenAIHandler, "interpretations", responses)
    monkeypatch.setattr(OpenAIHandler, "calls", [])
    return responses
