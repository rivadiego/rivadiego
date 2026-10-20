# Image of the Hugging Face Space: backend + web app, built by deploy/deploy_hf.py.
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
EXPOSE 7860
CMD ["python", "-m", "coach_connect", "serve", "--host", "0.0.0.0", "--port", "7860"]
