FROM python:3.9-slim

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip

RUN pip install --default-timeout=100 --retries=5 -r requirements.txt

COPY . .

ENV PYTHONPATH="/app:${PYTHONPATH}"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
