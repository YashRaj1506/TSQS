# Telemetry API

This project provides a FastAPI-based telemetry ingestion and query system with:

✅ Event ingestion (single + batch)
✅ Idempotency using `event_id`
✅ Query recent events per device
✅ Time-based aggregations (count, sum, avg, min, max)
✅ Search by tag
✅ Real-time alerts using Server-Sent Events (SSE)

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

## ✅ Stop Services
```
docker-compose down
```

---

## License
MIT

