"""
Serves the latest screener output to any frontend.
The heavy screening runs separately (via scheduler) and writes JSON to /output.
This API just reads and serves that JSON fast + lets you trigger a fresh run.

Run locally:   uvicorn api:app --reload --port 8000
Then call:     GET http://localhost:8000/recommendations/daily
                GET http://localhost:8000/recommendations/weekly
                POST http://localhost:8000/run/daily   (triggers a fresh screen)
"""

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import config
from screener import run_screen

app = FastAPI(title="Indian Stock Screener Agent")

# Allow any frontend to call this (tighten allow_origins for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "endpoints": ["/recommendations/daily", "/recommendations/weekly", "/run/{mode}"]}


@app.get("/recommendations/{mode}")
def get_recommendations(mode: str):
    if mode not in ("daily", "weekly"):
        raise HTTPException(400, "mode must be 'daily' or 'weekly'")
    path = f"{config.OUTPUT_DIR}/{mode}_screen.json"
    if not os.path.exists(path):
        raise HTTPException(404, f"No {mode} screen has been generated yet. POST /run/{mode} first.")
    with open(path) as f:
        return json.load(f)


@app.post("/run/{mode}")
def trigger_run(mode: str):
    if mode not in ("daily", "weekly"):
        raise HTTPException(400, "mode must be 'daily' or 'weekly'")
    result = run_screen(mode)
    return {"status": "completed", "shortlisted": len(result["shortlist"])}
