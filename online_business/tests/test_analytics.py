def test_seller_dashboard_empty(client, seller):
    r = client.get("/analytics/seller/dashboard", headers={"Authorization": f"Bearer {seller}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total_earnings"] == 0.0
    assert data["total_sales"] == 0
    assert data["total_products"] == 0
    assert data["top_products"] == []


def test_seller_dashboard_after_sale(client, buyer, seller):
    # Seller lists a product
    prod_r = client.post("/products", json={
        "title": "Analytics Test Product",
        "description": "For testing analytics.",
        "category": "ebook",
        "price": 20.00,
    }, headers={"Authorization": f"Bearer {seller}"})
    product = prod_r.json()

    # Buyer purchases it
    client.post("/orders", json={"product_id": product["id"], "payment_method_id": "pm_mock_card"},
                headers={"Authorization": f"Bearer {buyer}"})

    # Seller checks dashboard
    r = client.get("/analytics/seller/dashboard", headers={"Authorization": f"Bearer {seller}"})
    assert r.status_code == 200
    data = r.json()
    assert data["total_sales"] == 1
    assert data["total_earnings"] == round(20.00 * 0.85, 2)
    assert len(data["top_products"]) == 1
    assert data["top_products"][0]["title"] == "Analytics Test Product"


def test_health_check(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
