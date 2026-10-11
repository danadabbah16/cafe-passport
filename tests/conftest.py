import os
import tempfile

# Point the app at a throwaway database BEFORE importing it,
# so tests never touch data/cafe_passport.db
os.environ["DATA_DIR"] = tempfile.mkdtemp()

import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c