FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock \
    && groupadd --gid 10001 croquis3r \
    && useradd --uid 10001 --gid croquis3r --no-create-home croquis3r
COPY --chown=croquis3r:croquis3r manage.py ./
COPY --chown=croquis3r:croquis3r src ./src
RUN DJANGO_DEBUG=1 DB_ENGINE=sqlite python manage.py collectstatic --noinput
USER croquis3r
EXPOSE 8080
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
