FROM python:3.12.15-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN apt-get update \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir "pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70" \
    && python -m pip install --no-cache-dir -r requirements.lock \
    && python -m pip check \
    && groupadd --gid 10001 croquis3r \
    && useradd --uid 10001 --gid croquis3r --no-create-home croquis3r
COPY --chown=croquis3r:croquis3r manage.py ./
COPY --chown=croquis3r:croquis3r src ./src
RUN DJANGO_DEBUG=1 DB_ENGINE=sqlite python manage.py collectstatic --noinput
USER croquis3r
EXPOSE 8080
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--worker-class", "sync", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
