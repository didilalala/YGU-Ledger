FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod

WORKDIR /app

# 使用 PyMySQL（纯 Python），不需要安装 MySQL 客户端编译依赖
COPY requirements/base.txt requirements/base.txt
RUN pip install -r requirements/base.txt

COPY . .
RUN python manage.py collectstatic --noinput \
    && useradd --create-home app \
    && mkdir -p /app/media \
    && chown -R app /app
USER app

EXPOSE 8000

# 先执行迁移，再以 ASGI 方式启动（uvicorn worker 支持 AI 流式响应）
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.asgi:application -k uvicorn.workers.UvicornWorker -w ${GUNICORN_WORKERS:-2} -b 0.0.0.0:8000 --timeout 120 --access-logfile -"]
