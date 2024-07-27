from fastapi import FastAPI,Body
from typing import Any,Optional
from pydantic import BaseModel
import json
from src.text_to_action import ActionDispatcher
from dotenv import load_dotenv
load_dotenv()

class FunctionsRequest(BaseModel):
    text: str
    top_k: Optional[int]=5
    threshold: Optional[float] = 0.45

class ArgumentsRequest(BaseModel):
    text: str
    functions_args_dict:Any = Body(...)

app = FastAPI()

dispatcher = ActionDispatcher(action_embedding_filename="calculator.h5",actions_filepath=None,
                                use_llm_extract_parameters=True,verbose_output=True)


@app.post("/extract_functions")
async def extract_functions(request:FunctionsRequest):
    return dispatcher.extract_functions(query_text=request.text,
                                    top_k=request.top_k,threshold=request.threshold)

@app.post("/extract_arguments")
async def extract_arguments(request:ArgumentsRequest):

    if isinstance(request.functions_args_dict, str):
        try:
            functions_args_dict = json.loads(request.functions_args_dict)
        except json.JSONDecodeError:
            return {"error": "Invalid JSON for functions_args_dict"}
    else:
        functions_args_dict = request.functions_args_dict
    
    if isinstance(functions_args_dict, dict):
        return dispatcher.extract_parameters(query_text=request.text,
                                         functions_args_description=functions_args_dict
                                    )
    else:
        return json.dumps(dispatcher.extract_parameters(query_text=request.text,
                                            functions_args_description=functions_args_dict
                                        ))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)