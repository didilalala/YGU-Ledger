"""
生成演示数据：python manage.py seed_demo [--username demo] [--password demo123456]

用于论文演示、截图和手工验证界面。只会重建这个演示用户自己的数据，不影响其他用户；
重复执行得到相同的数据（固定随机种子，日期相对于今天）。
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q

from apps.accounts.models import Account
from apps.ai.models import AIModelConfig, ChatSession
from apps.ai.services.session import append_message
from apps.bills.models import Bill
from apps.budgets.models import Budget
from apps.categories.models import DEFAULT_CATEGORIES, Category
from apps.goals.models import FinancialGoal
from apps.users.models import User

# 分类 → (月均笔数, 单笔金额范围, 描述候选)
EXPENSE_PATTERNS = {
    "餐饮": (9, (12, 68), ["外卖", "午饭", "咖啡", "火锅", "早餐", "奶茶", "夜宵"]),
    "交通": (6, (3, 45), ["地铁", "打车", "公交", "加油", "共享单车"]),
    "购物": (3, (30, 380), ["日用品", "衣服", "网购", "超市"]),
    "娱乐": (2, (20, 160), ["电影", "游戏充值", "KTV"]),
    "医疗": (1, (25, 220), ["药店", "挂号费"]),
    "住房": (1, (1800, 2200), ["房租"]),
}
INCOME_PATTERNS = {"工资": (1, (7800, 8600), ["月薪"]), "兼职": (1, (200, 900), ["稿费", "家教"])}


class Command(BaseCommand):
    help = "生成演示用户和示例数据"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="demo123456")
        parser.add_argument("--months", type=int, default=12, help="生成最近多少个月的账单")

    @transaction.atomic
    def handle(self, *args, username, password, months, **options):
        rng = random.Random(20260318)
        today = date.today()

        user, created = User.objects.get_or_create(username=username, defaults={"nickname": "演示用户"})
        user.set_password(password)
        user.save()
        for model in (Bill, Budget, FinancialGoal, Account, AIModelConfig, ChatSession):
            model.objects.filter(user=user).delete()
        Category.objects.filter(user=user).delete()

        # 系统默认分类 + 两个自定义分类
        for order, (name, type_, icon) in enumerate(DEFAULT_CATEGORIES):
            Category.objects.get_or_create(user=None, name=name, type=type_,
                                           defaults={"icon": icon, "is_default": True, "sort_order": order})
        Category.objects.create(user=user, name="旅游", type="expense", icon="✈️", sort_order=20)
        Category.objects.create(user=user, name="电子器械", type="expense", icon="📺", sort_order=21)
        cats = {(c.name, c.type): c for c in Category.objects.filter(Q(user=user) | Q(user__isnull=True))}

        accounts = [
            Account.objects.create(user=user, name="工商银行储蓄卡", type="bank_card", balance=Decimal("12850.50"),
                                   is_default=True),
            Account.objects.create(user=user, name="微信零钱", type="e_wallet", balance=Decimal("436.20")),
            Account.objects.create(user=user, name="招商信用卡", type="credit_card", balance=Decimal("-2180.00")),
            Account.objects.create(user=user, name="现金", type="cash", balance=Decimal("300")),
        ]

        bills = []
        for back in range(months):
            first = (today.replace(day=1) - timedelta(days=30 * back)).replace(day=1)
            last_day = today.day if back == 0 else 28
            patterns = [(n, "expense", p) for n, p in EXPENSE_PATTERNS.items()] + \
                       [(n, "income", p) for n, p in INCOME_PATTERNS.items()]
            for name, type_, (per_month, (lo, hi), labels) in patterns:
                for _ in range(per_month):
                    day = first.replace(day=rng.randint(1, max(1, last_day)))
                    if day > today:
                        continue
                    bills.append(Bill(user=user, type=type_, category=cats[(name, type_)], date=day,
                                      amount=Decimal(str(round(rng.uniform(lo, hi), 2))),
                                      description=rng.choice(labels), account=rng.choice(accounts[:2]),
                                      source=rng.choice(["manual", "manual", "text", "notification"])))
        # 本月里固定几笔，方便首页截图稳定
        for days_ago, desc, name, amount in [(1, "外卖", "餐饮", "26.80"), (2, "地铁", "交通", "6.00"),
                                             (4, "杂志订阅", "娱乐", "35.00")]:
            bills.append(Bill(user=user, type="expense", category=cats[(name, "expense")], account=accounts[1],
                              date=today - timedelta(days=days_ago), amount=Decimal(amount), description=desc))
        bills.append(Bill(user=user, type="expense", category=cats[("旅游", "expense")], date=today - timedelta(days=40),
                          amount=Decimal("3776"), description="三亚机票酒店"))
        Bill.objects.bulk_create(bills)

        Budget.objects.create(user=user, name="餐饮预算", amount=Decimal("1500"), period="monthly",
                              category=cats[("餐饮", "expense")], alert_at=80)
        Budget.objects.create(user=user, name="本月总预算", amount=Decimal("4000"), period="monthly", alert_at=85)
        FinancialGoal.objects.create(user=user, name="旅行基金", target_amount=Decimal("8000"),
                                     current_amount=Decimal("3200"), icon="✈️",
                                     deadline=today + timedelta(days=120))
        FinancialGoal.objects.create(user=user, name="新手机", target_amount=Decimal("6000"),
                                     current_amount=Decimal("600"), icon="📱")

        config = AIModelConfig.objects.create(user=user, name="我的 DeepSeek", provider="deepseek",
                                              api_key="sk-demo-not-a-real-key", model="deepseek-chat",
                                              is_default=True)
        AIModelConfig.objects.create(user=user, name="Claude", provider="claude", api_key="sk-demo-not-a-real-key",
                                     model="claude-sonnet-5-5", supports_vision=True)

        session = ChatSession.objects.create(user=user, title="统计今年开销", ai_config=config)
        append_message(session, "user", content="帮我查下这个月花了多少")
        append_message(session, "assistant", content=None,
                       tool_calls=[{"id": "c1", "name": "get_statistics", "arguments": {}}])
        append_message(session, "tool", tool_call_id="c1", tool_name="get_statistics", tool_result={
            "success": True, "message": "统计数据获取成功",
            "data": {"total_expense": 301.34, "total_income": 600.0, "balance": 298.66}})
        append_message(session, "assistant", content="这个月你一共支出 ¥301.34，收入 ¥600.00，结余 ¥298.66。餐饮占比最大，要不要我帮你看看明细？")
        append_message(session, "user", content="中午吃饭花了32，打车18")
        ChatSession.objects.create(user=user, title="午饭记账", is_pinned=True)

        self.stdout.write(self.style.SUCCESS(
            f"{'已创建' if created else '已重置'}演示用户 {username} / {password}："
            f"{len(bills)} 笔账单、{len(accounts)} 个账户、2 个预算、2 个目标"))
