def _create_product(client, seller_token, price=19.99):
    r = client.post("/products", json={
        "title": "My Awesome Template",
        "description": "A great template for developers.",
        "category": "template",
        "price": price,
    }, headers={"Authorization": f"Bearer {seller_token}"})
    assert r.status_code == 201
    return r.json()


def test_create_product_as_seller(client, seller):
    p = _create_product(client, seller)
    assert p["title"] == "My Awesome Template"
    assert p["price"] == 19.99
    assert p["sales_count"] == 0


def test_create_product_as_buyer_forbidden(client, buyer):
    r = client.post("/products", json={
        "title": "Sneaky Product",
        "description": "Buyers cannot list products.",
        "category": "ebook",
        "price": 5.00,
    }, headers={"Authorization": f"Bearer {buyer}"})
    assert r.status_code == 403


def test_list_products(client, seller):
    _create_product(client, seller)
    r = client.get("/products")
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_filter_by_category(client, seller):
    _create_product(client, seller)
    r = client.get("/products?category=template")
    assert r.status_code == 200
    for p in r.json():
        assert p["category"] == "template"


def test_search_products(client, seller):
    _create_product(client, seller)
    r = client.get("/products?search=Awesome")
    assert r.status_code == 200
    assert any("Awesome" in p["title"] for p in r.json())


def test_get_product_by_id(client, seller):
    p = _create_product(client, seller)
    r = client.get(f"/products/{p['id']}")
    assert r.status_code == 200
    assert r.json()["id"] == p["id"]


def test_update_product(client, seller):
    p = _create_product(client, seller)
    r = client.patch(f"/products/{p['id']}", json={"price": 29.99},
                     headers={"Authorization": f"Bearer {seller}"})
    assert r.status_code == 200
    assert r.json()["price"] == 29.99


def test_delete_product(client, seller):
    p = _create_product(client, seller)
    r = client.delete(f"/products/{p['id']}", headers={"Authorization": f"Bearer {seller}"})
    assert r.status_code == 204
    r2 = client.get(f"/products/{p['id']}")
    assert r2.status_code == 404


def test_negative_price_rejected(client, seller):
    r = client.post("/products", json={
        "title": "Free Product",
        "description": "This should not be allowed.",
        "category": "tool",
        "price": -1.0,
    }, headers={"Authorization": f"Bearer {seller}"})
    assert r.status_code == 422
