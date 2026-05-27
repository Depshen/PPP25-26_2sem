from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_crud_lifecycle():
    market_resp = client.post(
        "/marketplaces/",
        json={"name": "Тестовый Маркет", "website_url": "https://test.ru"}
    )
    market_id = market_resp.json()["id"]

    post_resp = client.post(
        "/gadgets/",
        json={"title": "Test Phone", "brand": "BrandX", "current_price": 500.0, "marketplace_id": market_id}
    )
    assert post_resp.status_code == 201
    gadget_id = post_resp.json()["id"]

    get_resp = client.get(f"/gadgets/{gadget_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["title"] == "Test Phone"

    put_resp = client.put(
        f"/gadgets/{gadget_id}",
        json={"title": "Updated Phone", "brand": "BrandX", "current_price": 550.0, "marketplace_id": market_id}
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["title"] == "Updated Phone"

    patch_resp = client.patch(
        f"/gadgets/{gadget_id}/price",
        json={"current_price": 499.0}
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["current_price"] == 499.0

    del_resp = client.delete(f"/gadgets/{gadget_id}")
    assert del_resp.status_code == 204

def test_get_gadget_not_found():
    response = client.get("/gadgets/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Гаджет с запрошенным ID не обнаружен в базе"

def test_trigger_background_task():
    response = client.post("/tasks/recalc-stats/1")
    assert response.status_code == 200
    data = response.json()

    assert "task_id" in data
    assert data["status"] == "Задание успешно добавлено в фоновую очередь"