FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV DB_PATH=/tmp/tasks.db
EXPOSE 5000

RUN useradd -m appuser
USER appuser

CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "main:app"]
