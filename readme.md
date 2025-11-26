# Telemetry API

This project provides a FastAPI-based telemetry ingestion and query system with:

---

## 🚀 Getting Started

### Clone the Repository
```
git clone <your_repo_url>
cd <repo_folder>
```

### Create a .env and paste

```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/telemetry
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=telemetry

```

### Run with Docker
```
docker-compose up --build
```

This will start:

- FastAPI service
- PostgreSQL database

API will be available at:
```
http://localhost:8000
```

Docs:
```
http://localhost:8000/docs
```

---

## ✅ API Usage

### 1. Ingest Single Event
```
curl -X POST "http://localhost:8000/v1/events" \
-H "Content-Type: application/json" \
-d '{
  "event_id": "e001",
  "device_id": "deviceA",
  "timeStamp": "2025-01-15T10:00:00",
  "metrics": { "temp": 34.2, "cpu": 0.44 },
  "tags": ["room:101","sensor:v2"]
}'
```

Response:
```
{"status":"ok"}
```

---

### 2. Batch Ingest
```
curl -X POST "http://localhost:8000/v1/events/batch" \
-H "Content-Type: application/json" \
-d '[
  {
    "event_id": "e002",
    "device_id": "deviceA",
    "timeStamp": "2025-01-15T10:02:00",
    "metrics": { "temp": 30 },
    "tags": ["room:101"]
  },
  {
    "event_id": "e003",
    "device_id": "deviceA",
    "timeStamp": "2025-01-15T10:03:00",
    "metrics": { "temp": 35 },
    "tags": ["room:102"]
  }
]'
```

Each event returns:
```
{"event_id": "e002", "status": "stored"}
```
OR
```
{"event_id": "e002", "status": "duplicate"}
```

---

### 3. Query Recent Events
```
curl "http://localhost:8000/v1/devices/deviceA/events?from_time=2025-01-01T00:00:00&to_time=2025-12-31T00:00:00&limit=5"
```

---

### 4. Aggregations
```
curl "http://localhost:8000/v1/metrics/aggregate?metric=temp&device_id=deviceA&from_time=2025-01-01T00:00:00&to_time=2025-12-31T00:00:00&interval=1m"
```

Returns time buckets with:
- count
- sum
- avg
- min
- max

---

### 5. Search by Tag
```
curl "http://localhost:8000/v1/search?tag=room:101&from_time=2025-01-01T00:00:00&to_time=2025-12-31T00:00:00&limit=100"
```

---

## 🔔 Alerts (SSE)

### Start SSE Stream (listen for alerts)
```
curl "http://localhost:8000/v1/alerts/stream?device_id=deviceA"
```

This terminal will wait for alerts.

---

### Register Alert
```
curl -X POST "http://localhost:8000/v1/alerts" \
-H "Content-Type: application/json" \
-d '{
  "device_id":"deviceA",
  "metric":"temp",
  "op":">",
  "threshold":32
}'
```

---

### Trigger Alert
```
curl -X POST "http://localhost:8000/v1/events" \
-H "Content-Type: application/json" \
-d '{
  "event_id":"t002",
  "device_id":"deviceA",
  "timeStamp":"2025-01-15T11:01:00",
  "metrics":{"temp":40},
  "tags":[]
}'
```

Your SSE terminal will output:
```
data: {"device_id":"deviceA","metrics":{"temp":40},"time":"2025-01-15 11:01:00"}
```

---

## ✅ Features Implemented

- Idempotent event ingestion
- Batch ingestion
- Time range querying
- Tag search
- SQL aggregation
- Real-time alerting with SSE

---

## How we will scale it in production for millions of users

![System Architecture](max.png)

## 🏗️ System Workflow Overview

This system is designed to handle **high-volume metric ingestion**, **real-time alerting**, and **fast analytical queries** at scale.

---

### Metric Ingestion Flow

1. A user/device sends metrics to the ingestion API (`POST /v1/events`)
2. FastAPI **does NOT write to the database directly**
3. Instead, FastAPI pushes the incoming metrics into a **Redis Stream**

Redis Streams provide:

- high throughput buffering
- durability
- ability to handle spikes and millions of writes

---

### Ingestion Workers

Multiple ingestion worker processes continuously consume data from Redis Streams.

Workers perform:

- batch reading
- batching logic
- bulk inserts into **TimescaleDB**

Benefits:

- API stays fast and non-blocking
- database load is reduced
- throughput increases massively
- scaling is easy: just add more workers

---

###  Alert Distribution (Redis Pub/Sub)

- Workers keep an **in-memory cache of alert rules**
- When a user sets an alert (e.g., `temp > 32`) via:

POST /v1/alerts

Fastapi publishes the alert rule to **Redis Pub/Sub**

All workers are subscribed, so they:

- instantly receive the alert rule
- update their in-memory alert list
- no DB query required

As workers process incoming metrics:

- they compare metric values with alert rules
- if a metric exceeds a threshold:

worker publishes an alert event to Redis Pub/Sub,

fastapi has a sse endpoint, so when an alert comes

FastAPI pushes it to connected clients in real-time via SSE

--- 

## For queries like:

- tag search
- aggregations
- recent events

FastAPI interacts **directly with TimescaleDB**, not Redis.


---

## License
MIT

