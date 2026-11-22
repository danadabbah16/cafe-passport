FROM python:3.12.16-slim

ENV PORT=8000 \
    DATA_DIR=/data

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /data \
 && chown -R appuser:appuser /data /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py cafes.py seed.sql ./

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "app.py"]