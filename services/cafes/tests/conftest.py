import os
import uuid

import pymssql
import pytest

from db import parse_database_url

# Admin connection to a test SQL Server, e.g. mssql://sa:<password>@localhost:1433/master
ADMIN_URL = os.environ["TEST_ADMIN_URL"]
TEST_DB = f"cafes_test_{uuid.uuid4().hex[:8]}"


def _admin_exec(sql):
    conn = pymssql.connect(autocommit=True, **parse_database_url(ADMIN_URL))
    conn.cursor().execute(sql)
    conn.close()


# A fresh, throwaway database for this test run; the app must see it before import.
_admin_exec(f"CREATE DATABASE {TEST_DB}")
os.environ["DATABASE_URL"] = ADMIN_URL.rsplit("/", 1)[0] + "/" + TEST_DB

from app import app as flask_app  # noqa: E402


@pytest.fixture
def client():
    return flask_app.test_client()


@pytest.fixture(scope="session", autouse=True)
def drop_test_database():
    yield
    _admin_exec(f"ALTER DATABASE {TEST_DB} SET SINGLE_USER WITH ROLLBACK IMMEDIATE; "
                f"DROP DATABASE {TEST_DB}")