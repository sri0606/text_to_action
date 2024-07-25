import os
from dotenv import load_dotenv
load_dotenv()
import re
import json
import deepdiff
import ast
import inspect
from typing import get_args, List
from pydantic import BaseModel
from .types import LLM_API


class LLMClient:
    def __init__(self, api:LLM_API=LLM_API.GROQ, model="llama3-70b-8192"):
        
        if not isinstance(api, LLM_API):
            raise ValueError(f"api must be an instance of LLM_APIs Enum, got {type(api)}")
        self.api = api
        self.model = model
        self._check_env_api_key()
        self._load_api()
        
    def _check_env_api_key(self):
        if self.api == LLM_API.OPEN_AI and "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OPENAI_API_KEY environment variable is not set.")
        
        elif self.api == LLM_API.GROQ and "GROQ_API_KEY" not in os.environ:
            raise ValueError("GROQ_API_KEY environment variable is not set.")
            
    def _load_api(self):
        if self.api == LLM_API.OPEN_AI:
            from openai import OpenAI
            self.api_client = OpenAI()

        elif self.api == LLM_API.GROQ:
            from groq import Groq
            self.api_client = Groq()

    def get_response(self, prompt, messages=None):
        """
        Get a response from the LLM API.

        Args:
        prompt (str): The prompt to send to the LLM.
        messages (List[Dict[str, str]]): A list of messages to send to the LLM.
        """
        if messages is None:
            messages = [
                {
                    "role": "user",
                    "content": prompt,
                }
            ]

        chat_completion = self.api_client.chat.completions.create(
            messages=messages,
            model=self.model,
        )

        return chat_completion.choices[0].message.content
        


def create_instance(class_name: str, params: dict, param_type):
    if class_name == param_type.__name__:
        return param_type(**params)
    raise ValueError(f"Class name mismatch: expected {param_type.__name__}, got {class_name}")     

def are_objects_equal(json1, json2):
    diff = deepdiff.DeepDiff(json1, json2, ignore_order=True)
    return not bool(diff)


def parse_string_representation(s: str) -> tuple[str, dict]:
    try:
        node = ast.parse(s, mode='eval').body
        if isinstance(node, ast.Call):
            class_name = node.func.id
            params = {}
            for arg in node.keywords:
                try:
                    params[arg.arg] = ast.literal_eval(arg.value)
                except ValueError:
                    params[arg.arg] = ast.unparse(arg.value)
            return class_name, params
    except (SyntaxError, ValueError):
        pass
    return "", {}


def llm_extract_parameters(text: str, param_type,llm_client:LLMClient):
    """
    Extract parameters from the text using an LLM and initialize respective class.
    
    Args:
        text: The input text.
        param_type: The type of parameter to extract.

    Returns:
        List of instances of the class of type param_type
    """
    field_names = list(param_type.model_fields.keys())
    fields_example = ", ".join([f"{field}=value" for field in field_names])

    prompt = f"""
    Analyze the following text to extract information related to {param_type.__name__} ({param_type.description}).
    Focus on extracting values for these fields: {', '.join(field_names)}.
    Format the extracted information as Python code for initializing instances of the specified class.

    Text to analyze:
    {text}

    Expected Python code output format (follow this structure):
    [{param_type.__name__}({fields_example}), {param_type.__name__}({fields_example})]

    Ensure all extracted values are appropriate for the field types in {param_type.__name__}.
    If a field value is not found, omit it from the initialization.
    """

    result = llm_client.get_response(prompt)

    pattern = r"\w+\(.*?\)"
    class_initializations = re.findall(pattern, result)

    instances = []
    for class_init in class_initializations:
        class_name, params = parse_string_representation(class_init)
        try:
            instance = create_instance(class_name, params, param_type)
            instances.append(instance)
        except (ValueError, TypeError) as e:
            print(f"Error creating instance: {e}")

    return instances


def llm_map_pydantic_parameters(text: str, function_name: str, param_descriptions: str, extracted_parameters,llm_client:LLMClient):
    """
    Use an LLM to map extracted Pydantic models to function parameters.

    Args:
    text (str): The original input text.
    function_name (str): The name of the function to be executed.
    param_descriptions (str): A string describing the function's parameters.
    extracted_parameters (Dict[str, List[BaseModel]]): The extracted parameters as lists of Pydantic models.

    Returns:
    Dict[str, BaseModel]: A dictionary mapping parameter names to Pydantic model instances.
    """
    # Prepare a detailed description of the extracted parameters
    extracted_desc = ""
    for model_name, instances in extracted_parameters.items():
        extracted_desc += f"\n{model_name}:\n"
        for i, instance in enumerate(instances):
            extracted_desc += f"  Instance {i + 1}: {instance.json()}\n"


    prompt = f"""
    Given the following input text: "{text}"

    For the function "{function_name}" with the following parameters:
    {param_descriptions}

    And the following extracted parameters of Pydantic model types:
    {extracted_desc}

    Please map the extracted instances to the correct function parameters.
    If a parameter is not present in the extracted models, respond with "Not provided".
    Only return a JSON object where keys are parameter names and values are the mapped Pydantic model instances or "Not provided".
    Use "```" around the JSON object to ensure correct formatting so that i can directly do json.loads().""" 

    prompt += """
    Example output for a function "book_flight" with parameters 'start (GPE) and destination (GPE)':
        {
            "start": { "name": "New York"}, 
            "destination": { "name": "Los Angeles"}
        }
    """
    
    # Send prompt to LLM and get response
    llm_response = llm_client.get_response(prompt)
    # Parse LLM response
    try:
        json_obj = llm_response.split("```")[1].strip()
        mapped_params = json.loads(json_obj)
    except json.JSONDecodeError:
        print(f"Error: LLM response is not valid JSON: {llm_response}")
        return {}

    # Convert the mapped parameters back to Pydantic models
    result = {}
    for param_name, param_value in mapped_params.items():
        if param_value == "Not provided":
            result[param_name] = None
        else:
            for model_name, instances in extracted_parameters.items():
                for instance in instances:
                    if are_objects_equal(instance.model_dump(), param_value):
                        result[param_name] = instance
                        break
                if param_name in result:
                    break
            if param_name not in result:
                print(f"Warning: Could not find matching Pydantic model for parameter {param_name}")

    return result


def llm_extract_all_parameters(function_name, query_text,llm_client:LLMClient):
    """
    Extract all parameters for a given function using an LLM and map them to correct kwargs.
    
    Args:
        function_name: The function for which to extract parameters.
        query_text: The input text to analyze for parameter extraction.

    Returns:
        A JSON string containing the extracted parameters mapped to their correct kwargs.
    """
    # Get the signature of the function
    sig = inspect.signature(function_name)

    param_dict = {}
    type_descriptions = {}

    for param_name, param in sig.parameters.items():
        param_type = param.annotation
        if hasattr(param_type, '__origin__') and param_type.__origin__ is list:
            inner_type = get_args(param_type)[0]
            type_name = f"List[{inner_type.__name__}]"
            param_dict[param_name] = type_name
            if issubclass(inner_type, BaseModel):
                field_descriptions = {field: field_info.description for field, field_info in inner_type.model_fields.items()}
                type_descriptions[type_name] = {
                    "description": f"A list of {inner_type.__name__} objects",
                    "fields": field_descriptions
                }
            else:
                type_descriptions[type_name] = {
                    "description": f"A list of {inner_type.__name__} values"
                }
        elif issubclass(param_type, BaseModel):
            type_name = param_type.__name__
            param_dict[param_name] = type_name
            field_descriptions = {field: field_info.description for field, field_info in param_type.model_fields.items()}
            type_descriptions[type_name] = {
                "description": param_type.description,
                "fields": field_descriptions
            }
        else:
            type_name = param_type.__name__
            param_dict[param_name] = type_name
            type_descriptions[type_name] = {
                "description": f"A single {type_name} value"
            }

    prompt = f"""
    Analyze the following text to extract parameters for the function "{function_name.__name__}".
    The function takes the following parameters:
        {json.dumps(param_dict, indent=2)}

    Where each parameter type description is as follows:
        {json.dumps(type_descriptions, indent=2)}

    Text to analyze:
    "{query_text}"

    Extract the values for each parameter and only return a JSON object where the keys are the parameter names and the values are the extracted values.
    For List types, provide a list of values.
    For complex types (like Pydantic models), provide a dictionary with the field names as keys.
    If a value for a parameter is not found, omit it from the JSON.
    Use "```" around the JSON object to ensure correct formatting so that I can directly do json.loads().
    Expected JSON output format:
    {{
        "param_name1": value1,
        "param_name2": [value2a, value2b],
        "param_name3": {{"field1": value3a, "field2": value3b}}
    }}
    """
    # return prompt
    # Send prompt to LLM and get the response
    llm_response = llm_client.get_response(prompt)

    # return llm_response
    # Parse the JSON response
    try:
        json_obj = llm_response.split("```")[1].strip()
        extracted_params = json.loads(json_obj)
    except json.JSONDecodeError:
        print("Error: LLM response is not valid JSON")
        return "{}"

    # Validate and convert the extracted parameters
    validated_params = {}
    for param_name, param in sig.parameters.items():
        if param_name in extracted_params:
            param_type = param.annotation
            if hasattr(param_type, '__origin__') and param_type.__origin__ is list:
                inner_type = get_args(param_type)[0]
                if issubclass(inner_type, BaseModel):
                    validated_params[param_name] = [inner_type(**item) for item in extracted_params[param_name]]
                else:
                    validated_params[param_name] = extracted_params[param_name]
            elif issubclass(param_type, BaseModel):
                validated_params[param_name] = param_type(**extracted_params[param_name])
            else:
                validated_params[param_name] = extracted_params[param_name]

    return validated_params
    