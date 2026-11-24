def test_budget_starts_empty_then_saves_and_updates(client):
    assert client.get("/budget").get_json() == {"monthly_goal": None}

    assert client.put("/budget", json={"monthly_goal": 50}).status_code == 200
    assert client.get("/budget").get_json()["monthly_goal"] == 50

    assert client.put("/budget", json={"monthly_goal": 80}).status_code == 200
    assert client.get("/budget").get_json()["monthly_goal"] == 80


def test_budget_rejects_bad_values(client):
    assert client.put("/budget", json={"monthly_goal": -5}).status_code == 400
    assert client.put("/budget", json={"monthly_goal": "abc"}).status_code == 400