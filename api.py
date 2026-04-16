from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from agent import creer_agent


app = FastAPI(title="TP Agent API")


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class QueryResponse(BaseModel):
    output: str


@app.post("/api/agent/query", response_model=QueryResponse)
def query_agent(req: QueryRequest, request: Request) -> QueryResponse:

    agent = creer_agent()

    try:
        result = agent.invoke({"input": req.question})
        output = result.get("output", "")
        return QueryResponse(output=output)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
