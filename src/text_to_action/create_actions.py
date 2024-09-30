from .vector_emb import VectorStore, ModelSource
import json
from .types import validate_functions

def create_actions_embeddings(functions_description_filepath:str, save_to:str, validate_data:bool=False,
                              embedding_model:str="all-MiniLM-L6-v2",model_source=ModelSource.SBERT):
    """
    Creates embeddings (VectorStore) for the given functions_description and saves it to a file (.h5).

    Args:
        functions_description_filepath: Path to the JSON file containing the functions description (**should strictly be same format as described in example below.**)
        save_to: The name or path of the file to save the embeddings to.
        validate_data: Optionally, you can validate the functions description data to check if they are in correct format and expected types.
        embedding_model: The name of the embedding model.
        model_soruce: Either SBERT or a huggin face model.

    Example:
        functions_description = { 

            "add": {
                    "description": "Add or sum a list of numbers",
                    "examples": ["20+50", "add 10, 30, 69", "sum of 1,3,4", "combine numbers", "find the total"]
                    "args" : {
                            "values" : {"type": "List[int]","required": True}
                            }
            },

            "subtract":{
                    "description": "Subtract a number from a number",
                    "examples": ["What is 10 minus 4?"]},
                    "args" : {
                                "a" : {"type": "int","required": True},
                                "b" : {"type": "int","required": True}
                            }
            }
    """
    with open(functions_description_filepath, 'r') as f:
        functions_description = json.load(f)

    if validate_data:
        invalid_data = validate_functions(functions_description)
        if len(invalid_data)>0:
            raise ValueError(f"Invalid function descriptions found: {', '.join(invalid_data)}") 

    store = VectorStore(embedding_model=embedding_model,model_source=model_source)
    for function_name, details in functions_description.items():
        store.add_vector(text=details["description"],id_name=function_name)
        for prompt in details["examples"]:
            store.add_vector(text=prompt,id_name=function_name)

    store.save(save_to)

    return
    
if __name__ == '__main__':
    import time
    import os
    # Get the directory of the current file
    current_directory = os.path.dirname(os.path.abspath(__file__))
    descriptions_filepath = os.path.join(current_directory,"example_actions", "calculator", "descriptions.json")
    save_to = os.path.join(current_directory,"example_actions", "calculator", "embeddings.h5")
    initial_time = time.time()
    create_actions_embeddings(descriptions_filepath, save_to=save_to,validate_data=True)
    print("\n================================")
    print("Creating embeddings took: " + str(time.time() - initial_time , "seconds"))