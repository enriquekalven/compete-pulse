from fastapi import FastAPI, Query
from typing import List, Dict, Any, Optional
from .agent import CompetePulseAgent

app = FastAPI(title="Compete Pulse Agent API", version="0.1.0-RAG")
agent = CompetePulseAgent()

@app.get("/")
def read_root():
    return {"message": "Compete Pulse Agent API is active", "status": "healthy"}

@app.get("/query")
def query_agent(q: str = Query(..., description="The search query for the AI knowledge base")):
    results = agent.query_knowledge(q)
    return {"query": q, "results": results}

@app.get("/pulse")
def get_pulse(days: int = 1):
    knowledge = agent.browse_knowledge()
    from .agent import parse_date
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    filtered = [item for item in knowledge if parse_date(item.get('date', '')) >= cutoff]
    synthesized = agent.synthesize_reports(filtered)
    return synthesized
