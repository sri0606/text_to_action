from fastapi import FastAPI,Body
from typing import Any,Optional, Dict
from pydantic import BaseModel
import json
import os
from src.text_to_action import TextToAction, LLMClient
from dotenv import load_dotenv
load_dotenv()


class FunctionsRequest(BaseModel):
    text: str
    top_k: Optional[int]=5
    threshold: Optional[float] = 0.45

class ArgumentsRequest(BaseModel):
    text: str
    action_name: str
    args: Dict[str,Dict[str,Any]]

app = FastAPI()

llm_client = LLMClient(model="groq/mixtral-8x7b-32768")
current_directory = os.path.dirname(os.path.abspath(__file__))
calculator_actions_folder = os.path.join(current_directory,"src","text_to_action","example_actions","calculator")

dispatcher = TextToAction(actions_folder = calculator_actions_folder, llm_client=llm_client,
                            verbose_output=True,application_context="Calculator", filter_input=True)

@app.post("/extract_actions")
async def extract_actions(request:FunctionsRequest):
    result =  dispatcher.extract_actions(query_text=request.text,
                                    top_k=request.top_k,threshold=request.threshold)

    return json.dumps(result)

@app.post("/extract_arguments")
async def extract_arguments(request:ArgumentsRequest):
    result = dispatcher.extract_parameters(query_text=request.text, action_name=request.action_name, args = request.args)

    return json.dumps(result)
         
@app.post("/extract_actions_with_args")
async def extract(request:FunctionsRequest):
    result =  dispatcher.extract_actions_with_args(query_text=request.text,
                                    top_k=request.top_k,threshold=request.threshold)

    return json.dumps(result)

@app.post("/run")
async def run( request:FunctionsRequest):
    result =  dispatcher.run(query_text=request.text,
                                    top_k=request.top_k,threshold=request.threshold)

    return json.dumps(result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)