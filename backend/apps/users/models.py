import uuid

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        if not username:
            raise ValueError("用户名不能为空")
        user = self.model(username=username.lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        return self.create_user(username, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    """对应 Prisma 模型 User。主键沿用 UUID。"""

    id = models.UUIDField("用户ID", primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField("用户名", max_length=50, unique=True)
    email = models.EmailField("邮箱", max_length=100, unique=True, null=True, blank=True)
    nickname = models.CharField("昵称", max_length=50, null=True, blank=True)
    avatar = models.TextField("头像URL", null=True, blank=True)
    is_active = models.BooleanField("是否激活", default=True)
    is_staff = models.BooleanField("可登录后台", default=False)
    last_login = models.DateTimeField("最后登录时间", null=True, blank=True, db_column="last_login_at")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = verbose_name_plural = "用户"

    def __str__(self):
        return self.username
