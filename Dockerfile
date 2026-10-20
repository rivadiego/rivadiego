# Image of the online service (Render): backend + web app, from the branch prepared by deploy/deploy.py.
FROM python:3.12-slim

RUN useradd --create-home --uid 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    WEB_DIR=/home/user/app/web \
    DB_PATH=/home/user/app/data/garmin.db \
    GARMIN_TOKEN_DIR=/home/user/app/data/garmin-tokens
WORKDIR /home/user/app

COPY --chown=user backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --user -r backend/requirements.txt
COPY --chown=user backend backend
COPY --chown=user web web

WORKDIR /home/user/app/backend
EXPOSE 10000
# exec: the server gets SIGTERM directly and saves pending changes before the instance stops.
CMD ["sh", "-c", "exec python -m coach_connect serve --host 0.0.0.0 --port ${PORT:-10000}"]
