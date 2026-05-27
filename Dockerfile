FROM node:22-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    DJANGO_DEBUG=False \
    DJANGO_ALLOWED_HOSTS="*" \
    FRONTEND_DIST=/home/user/app/backend/frontend_dist

RUN useradd -m -u 1000 user

WORKDIR /home/user/app

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=user:user backend ./backend
COPY --from=frontend-build --chown=user:user /app/frontend/dist ./backend/frontend_dist
COPY --chown=user:user hf-start.sh ./hf-start.sh

RUN chmod +x ./hf-start.sh

USER user
WORKDIR /home/user/app/backend

EXPOSE 7860

CMD ["/home/user/app/hf-start.sh"]
