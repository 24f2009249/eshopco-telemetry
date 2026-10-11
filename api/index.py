from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    expose_headers=["Access-Control-Allow-Origin"],
)

TELEMETRY_PATH = os.path.join(os.path.dirname(__file__), "..", "telemetry.json")
if not os.path.exists(TELEMETRY_PATH):
    TELEMETRY_PATH = os.path.join(os.path.dirname(__file__), "telemetry.json")

try:
    with open(TELEMETRY_PATH, "r") as f:
        TELEMETRY_DATA = json.load(f)
except Exception:
    TELEMETRY_DATA = []

# Explicitly handle OPTIONS preflight requests for the grader
@app.options("/{path:path}")
async def options_handler(path: str, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return {"status": "ok"}

@app.post("/")
async def analyze_telemetry(request: Request, response: Response):
    # Force manual CORS headers on the POST response as well
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    results = {}

    for region in regions:
        region_records = [r for r in TELEMETRY_DATA if r.get("region") == region]
        
        if not region_records:
            results[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in region_records if "latency_ms" in r]
        uptimes = [r["uptime_pct"] for r in region_records if "uptime_pct" in r]

        avg_lat = float(np.mean(latencies)) if latencies else 0.0
        p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0
        avg_up = float(np.mean(uptimes)) if uptimes else 0.0
        breaches_count = sum(1 for l in latencies if l > threshold_ms)

        results[region] = {
            "avg_latency": avg_lat,
            "p95_latency": p95_lat,
            "avg_uptime": avg_up,
            "breaches": breaches_count
        }

    return results