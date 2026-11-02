FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 1001 study \
    && useradd --uid 1000 --gid 1001 --home-dir /home/ubuntu --create-home --shell /usr/sbin/nologin study \
    && install -d -m 0700 -o 1000 -g 1001 /home/ubuntu/.ssh
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOME=/home/ubuntu
USER 1000:1001
WORKDIR /app
ENTRYPOINT ["python3", "-m", "web.server.app", "--host", "127.0.0.1", "--port", "8183"]
