FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DEALBRINGER_DATA_DIR=/data
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --uid 10001 --create-home app \
    && mkdir /data && chown app:app /data
USER app
VOLUME ["/data"]
ENTRYPOINT ["dealbringer"]
CMD ["run", "fake"]
