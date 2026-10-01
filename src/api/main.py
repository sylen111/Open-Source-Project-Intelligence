from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.agent.graph import graph


app = FastAPI()


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    initial_state = {
        "user_query": request.query,
        "messages": [
            {
                "role": "user",
                "content": request.query
            }
        ],
        "tool_results": [],
        "final_answer": None,
        "iterations": 0
    }

    try:
        result = graph.invoke(initial_state)

        return {
            "answer": result["final_answer"]
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Agent execution failed"
        )