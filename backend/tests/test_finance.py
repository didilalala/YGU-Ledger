from apps.categories.models import Category


def _create_bill(client, **overrides):
    data = {"amount": 25.5, "type": "expense", "date": "2026-10-01", "description": "午饭", **overrides}
    resp = client.post("/api/bills", data, format="json")
    assert resp.status_code == 201, resp.json()
    return resp.json()["data"]


def test_bill_crud(client):
    food = Category.objects.create(name="餐饮", type="expense", is_default=True)
    bill = _create_bill(client, categoryId=food.id, tags=["工作日"])
    assert bill["amount"] == 25.5
    assert bill["category"]["name"] == "餐饮"
    assert bill["tags"] == ["工作日"]

    resp = client.patch(f"/api/bills/{bill['id']}", {"amount": 30}, format="json")
    assert resp.json()["data"]["amount"] == 30

    resp = client.delete(f"/api/bills/{bill['id']}")
    assert resp.status_code == 200 and resp.json()["message"] == "删除成功"
    assert client.get(f"/api/bills/{bill['id']}").status_code == 404


def test_bill_list_pagination_and_camelcase_filters(client):
    _create_bill(client, date="2026-09-30")
    _create_bill(client, date="2026-10-02")
    _create_bill(client, date="2026-10-03", type="income", amount=100)

    data = client.get("/api/bills", {"startDate": "2026-10-01", "type": "expense"}).json()["data"]
    assert data["pagination"]["total"] == 1
    assert data["pagination"]["hasNext"] is False
    assert data["items"][0]["date"] == "2026-10-02"


def test_users_cannot_see_each_others_data(client, other_client):
    bill = _create_bill(client)
    assert other_client.get(f"/api/bills/{bill['id']}").status_code == 404
    assert other_client.get("/api/bills").json()["data"]["pagination"]["total"] == 0


def test_cannot_use_another_users_category(client, other_client):
    cat = other_client.post("/api/categories", {"name": "私有", "type": "expense"}, format="json").json()["data"]
    resp = client.post("/api/bills", {"amount": 1, "type": "expense", "date": "2026-10-01",
                                      "categoryId": cat["id"]}, format="json")
    assert resp.status_code == 400


def test_categories_include_system_defaults(client):
    Category.objects.create(name="餐饮", type="expense", is_default=True)
    client.post("/api/categories", {"name": "宠物", "type": "expense"}, format="json")
    names = {c["name"] for c in client.get("/api/categories", {"type": "expense"}).json()["data"]}
    assert names == {"餐饮", "宠物"}


def test_statistics(client):
    food = Category.objects.create(name="餐饮", type="expense", is_default=True)
    _create_bill(client, amount=30, categoryId=food.id, date="2026-10-01")
    _create_bill(client, amount=10, date="2026-10-01")
    _create_bill(client, amount=1000, type="income", date="2026-10-05")

    stats = client.get("/api/bills/statistics", {"startDate": "2026-10-01", "endDate": "2026-10-31"}).json()["data"]
    assert stats["totalIncome"] == 1000
    assert stats["totalExpense"] == 40
    assert stats["balance"] == 960
    assert stats["expenseByCategory"][0] == {
        "categoryId": food.id, "categoryName": "餐饮", "categoryIcon": "📊",
        "amount": 30.0, "percentage": 75.0, "count": 1,
    }
    assert [t["period"] for t in stats["trend"]] == ["2026-10-01", "2026-10-05"]


def test_budget_progress(client):
    from datetime import date

    today = date.today().isoformat()
    client.post("/api/budgets", {"name": "月度总预算", "amount": 100, "period": "monthly", "alertAt": 50},
                format="json")
    _create_bill(client, amount=60, date=today)
    item = client.get("/api/budgets/progress").json()["data"][0]
    assert item["spent"] == 60 and item["percentage"] == 60.0
    assert item["isAlert"] is True and item["isOverBudget"] is False


def test_account_balance(client):
    client.post("/api/accounts", {"name": "银行卡", "type": "bank_card", "balance": 100.5}, format="json")
    client.post("/api/accounts", {"name": "现金", "type": "cash", "balance": 20}, format="json")
    assert client.get("/api/accounts/balance").json()["data"]["totalBalance"] == 120.5
