FROM python:3.12.16-slim

ENV PORT=8000

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser \
 && chown -R appuser:appuser /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py db.py cafes.py seed.sql ./
COPY migrations/ ./migrations/

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["python", "app.py"]