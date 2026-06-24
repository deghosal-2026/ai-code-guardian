"""FastAPI dashboard server for Guardian metrics."""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

app = FastAPI(title="AI Code Guardian Dashboard")
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/api/stats")
async def api_stats():
    return {"status": "coming soon"}


@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest
    return generate_latest()
