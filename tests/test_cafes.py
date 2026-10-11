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

def test_rankings_endpoint_returns_list(client):
    client.post("/cafes/2/visits",
                json={"visit_date": "2026-10-10", "drink": "espresso", "price": 2.5, "rating": 9})
    r = client.get("/rankings")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)