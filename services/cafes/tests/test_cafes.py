def test_health(client):
    assert client.get("/health").status_code == 200

def test_create_cafe(client):
    r = client.post("/cafes", json={"name": "Test Cafe A", "city": "Madrid"})
    assert r.status_code == 201
    assert r.get_json()["name"] == "Test Cafe A"

def test_duplicate_cafe_rejected(client):
    client.post("/cafes", json={"name": "Dup Cafe", "city": "Madrid"})
    r = client.post("/cafes", json={"name": "Dup Cafe", "city": "Madrid"})
    assert r.status_code == 409

def test_cafe_requires_name_and_city(client):
    assert client.post("/cafes", json={"name": "No City"}).status_code == 400

def test_visit_unknown_cafe_is_404(client):
    r = client.post("/cafes/9999/visits",
                    json={"visit_date": "2026-10-11", "drink": "latte", "price": 3, "rating": 7})
    assert r.status_code == 404

def test_visit_rating_out_of_range_is_400(client):
    r = client.post("/cafes/1/visits",
                    json={"visit_date": "2026-10-11", "drink": "latte", "price": 3, "rating": 15})
    assert r.status_code == 400

def test_log_and_list_visit(client):
    r = client.post("/cafes/1/visits",
                    json={"visit_date": "2026-10-11", "drink": "cortado", "price": 3.0, "rating": 8})
    assert r.status_code == 201
    listed = client.get("/cafes/1/visits").get_json()
    assert any(v["drink"] == "cortado" for v in listed)

def test_list_all_visits(client):
    client.post("/cafes/1/visits",
                json={"visit_date": "2026-11-01", "drink": "latte", "price": 3.5, "rating": 8})
    r = client.get("/visits")
    assert r.status_code == 200
    visits = r.get_json()
    assert any(v["cafe_id"] == 1 and v["drink"] == "latte" for v in visits)


def test_health_is_503_when_db_unavailable(client, monkeypatch):
    import app as app_module

    def db_down():
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(app_module, "check_db", db_down)
    r = client.get("/health")
    assert r.status_code == 503
    assert r.get_json()["db"] == "unavailable"