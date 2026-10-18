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


def test_account_balance_splits_assets_and_liabilities(client):
    client.post("/api/accounts", {"name": "银行卡", "type": "bank_card", "balance": 100.5}, format="json")
    client.post("/api/accounts", {"name": "现金", "type": "cash", "balance": 20}, format="json")
    client.post("/api/accounts", {"name": "信用卡", "type": "credit_card", "balance": -300}, format="json")
    data = client.get("/api/accounts/balance").json()["data"]
    assert data == {"totalAssets": 120.5, "totalLiabilities": 300.0, "netWorth": -179.5}


def test_only_one_default_account(client, other_client):
    def create(name, **kw):
        return client.post("/api/accounts", {"name": name, "type": "cash", **kw}, format="json").json()["data"]

    a = create("A", isDefault=True)
    b = create("B", isDefault=True)  # 新建时设为默认，A 应被取消
    defaults = lambda: [x["name"] for x in client.get("/api/accounts").json()["data"] if x["isDefault"]]  # noqa: E731
    assert defaults() == ["B"]

    client.patch(f"/api/accounts/{a['id']}", {"isDefault": True}, format="json")  # 修改时设为默认，B 应被取消
    assert defaults() == ["A"]

    client.patch(f"/api/accounts/{a['id']}", {"name": "A2"}, format="json")  # 改其他字段不影响默认
    assert defaults() == ["A2"]

    # 别人的默认账户不受影响
    other_client.post("/api/accounts", {"name": "X", "type": "cash", "isDefault": True}, format="json")
    client.patch(f"/api/accounts/{b['id']}", {"isDefault": True}, format="json")
    assert [x["name"] for x in other_client.get("/api/accounts").json()["data"] if x["isDefault"]] == ["X"]


def test_accounts_listed_default_first(client):
    for name in ("先建", "后建"):
        client.post("/api/accounts", {"name": name, "type": "cash"}, format="json")
    client.post("/api/accounts", {"name": "默认", "type": "bank_card", "isDefault": True}, format="json")
    assert [x["name"] for x in client.get("/api/accounts").json()["data"]] == ["默认", "后建", "先建"]


# ---------------------------------------------------------------- 目标

def test_goal_crud_and_progress(client, other_client):
    created = client.post("/api/financial-goals", {"name": "旅行基金", "targetAmount": 5000, "currentAmount": 1250,
                                                  "deadline": "2027-01-01", "icon": "✈️"}, format="json")
    assert created.status_code == 201
    goal = created.json()["data"]
    assert goal["progress"] == 25.0 and goal["isCompleted"] is False

    patched = client.patch(f"/api/financial-goals/{goal['id']}",
                           {"currentAmount": 6000, "isCompleted": True, "deadline": None}, format="json").json()["data"]
    assert patched["progress"] == 100.0 and patched["isCompleted"] is True and patched["deadline"] is None

    summary = client.get("/api/financial-goals/progress").json()["data"]
    assert summary["totalGoals"] == 1 and summary["completedGoals"] == 1 and summary["overallProgress"] == 120.0

    # 别人看不到、改不了、删不掉
    assert other_client.get("/api/financial-goals").json()["data"] == []
    assert other_client.patch(f"/api/financial-goals/{goal['id']}", {"name": "x"}, format="json").status_code == 404
    assert other_client.delete(f"/api/financial-goals/{goal['id']}").status_code == 404

    assert client.delete(f"/api/financial-goals/{goal['id']}").json()["message"] == "删除成功"
    assert client.get("/api/financial-goals").json()["data"] == []


def test_goal_rejects_negative_amount(client):
    resp = client.post("/api/financial-goals", {"name": "x", "targetAmount": -1}, format="json")
    assert resp.status_code == 400 and resp.json()["success"] is False


# ---------------------------------------------------------------- 分类

def test_custom_category_edit_and_delete(client, other_client):
    cat = client.post("/api/categories", {"name": "宠物", "type": "expense", "icon": "🐶"}, format="json").json()["data"]
    assert cat["isDefault"] is False

    renamed = client.patch(f"/api/categories/{cat['id']}", {"name": "宠物用品", "icon": None}, format="json")
    assert renamed.status_code == 200 and renamed.json()["data"]["name"] == "宠物用品"

    # 别人的分类看不到，也不能改
    assert cat["id"] not in [c["id"] for c in other_client.get("/api/categories").json()["data"]]
    assert other_client.patch(f"/api/categories/{cat['id']}", {"name": "x"}, format="json").status_code == 404
    assert other_client.delete(f"/api/categories/{cat['id']}").status_code == 404

    assert client.delete(f"/api/categories/{cat['id']}").status_code == 200
    assert cat["id"] not in [c["id"] for c in client.get("/api/categories").json()["data"]]


def test_default_category_is_read_only(client):
    from apps.categories.models import Category

    default = Category.objects.create(user=None, name="餐饮", type="expense", icon="🍔", is_default=True)
    assert default.id in [c["id"] for c in client.get("/api/categories").json()["data"]]  # 看得到
    assert client.patch(f"/api/categories/{default.id}", {"name": "x"}, format="json").status_code == 404
    assert client.delete(f"/api/categories/{default.id}").status_code == 404
    default.refresh_from_db()
    assert default.name == "餐饮"


def test_deleting_category_keeps_bills_uncategorized(client):
    cat = client.post("/api/categories", {"name": "临时", "type": "expense"}, format="json").json()["data"]
    bill = client.post("/api/bills", {"amount": 10, "type": "expense", "date": "2026-10-01",
                                      "categoryId": cat["id"]}, format="json").json()["data"]
    client.delete(f"/api/categories/{cat['id']}")
    after = client.get(f"/api/bills/{bill['id']}").json()["data"]
    assert after["category"] is None  # 账单还在，只是变成未分类


# ---------------------------------------------------------------- 预算

def test_budget_validation(client, other_client):
    base = {"name": "餐饮", "amount": 1000, "period": "monthly"}
    assert client.post("/api/budgets", {**base, "alertAt": 0}, format="json").status_code == 400
    assert client.post("/api/budgets", {**base, "alertAt": 101}, format="json").status_code == 400
    assert client.post("/api/budgets", {**base, "period": "weekly"}, format="json").status_code == 400
    assert client.post("/api/budgets", {**base, "amount": -5}, format="json").status_code == 400
    # 不能把预算挂到别人的分类上
    theirs = other_client.post("/api/categories", {"name": "私有", "type": "expense"}, format="json").json()["data"]
    assert client.post("/api/budgets", {**base, "categoryId": theirs["id"]}, format="json").status_code == 400
    assert client.post("/api/budgets", {**base, "alertAt": 100}, format="json").status_code == 201


def test_inactive_budget_listed_but_not_in_progress(client):
    budget = client.post("/api/budgets", {"name": "总预算", "amount": 2000, "period": "monthly"},
                         format="json").json()["data"]
    client.patch(f"/api/budgets/{budget['id']}", {"isActive": False}, format="json")
    assert [b["id"] for b in client.get("/api/budgets").json()["data"]] == [budget["id"]]
    assert client.get("/api/budgets/progress").json()["data"] == []  # 前端要自己从 list 补上停用的预算
    client.patch(f"/api/budgets/{budget['id']}", {"isActive": True}, format="json")
    assert len(client.get("/api/budgets/progress").json()["data"]) == 1


def test_statistics_monthly_trend_with_category_filter(client):
    food = Category.objects.create(name="餐饮", type="expense", is_default=True)
    _create_bill(client, amount=30, categoryId=food.id, date="2026-09-20")
    _create_bill(client, amount=50, categoryId=food.id, date="2026-10-02")
    _create_bill(client, amount=999, date="2026-10-03")  # 无分类，筛选时不应计入
    _create_bill(client, amount=1000, type="income", date="2026-10-05")

    monthly = client.get("/api/bills/statistics", {"granularity": "monthly"}).json()["data"]
    assert {t["period"]: t["expense"] for t in monthly["trend"]} == {"2026-09": 30.0, "2026-10": 1049.0}

    filtered = client.get("/api/bills/statistics", {"granularity": "monthly", "categoryId": food.id}).json()["data"]
    assert {t["period"]: t["expense"] for t in filtered["trend"]} == {"2026-09": 30.0, "2026-10": 50.0}
    assert filtered["totalExpense"] == 80 and filtered["totalIncome"] == 0


def test_bill_patch_partial_update(client, other_client):
    food = Category.objects.create(name="餐饮", type="expense", is_default=True)
    bill = _create_bill(client, amount=30, categoryId=food.id, date="2026-10-01", description="午饭")
    bill_id = bill["id"]

    resp = client.patch(f"/api/bills/{bill_id}", {"amount": 35.5, "categoryId": None}, format="json")
    data = resp.json()["data"]
    assert resp.status_code == 200 and data["amount"] == 35.5 and data["category"] is None
    assert data["description"] == "午饭" and data["date"] == "2026-10-01"  # 没传的字段保持不变

    # 不能越权修改别人的账单
    assert other_client.patch(f"/api/bills/{bill_id}", {"amount": 1}, format="json").status_code == 404
