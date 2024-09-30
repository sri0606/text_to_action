import os
from dotenv import load_dotenv
load_dotenv()
import re
import json
import deepdiff
import ast
import inspect
from typing import get_args
from pydantic import BaseModel
from openai import OpenAIError, OpenAI
from litellm import completion

class ConversationManager:
    def __init__(self, max_history=10):
        """
        Initialize the ConversationManager.

        Args:
            max_history: Maximum number of messages to keep in conversation history.
        """
        self.max_history = max_history
        self.system_message = {"role": "system", "content": "You are a helpful assistant."}
        self.conversation_history = []

    def set_system_message(self, content):
        """Set or update the system message."""
        self.system_message["content"] = content

    def add_to_history(self, role, content):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]

    def get_messages(self, include_history=True):
        """
        Get messages for the LLM API call.

        Args:
        include_history (bool): Whether to include conversation history.
        """
        messages = [self.system_message]
        if include_history:
            messages.extend(self.conversation_history)
        return messages

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history = []

class LLMClient:
    def __init__(self,  model="gpt-3.5-turbo", local_llm_endpoint=None):
        """
        Args:
            model: LLM model name. (Find supported models here: https://docs.litellm.ai/docs/providers)
            local_llm_endpoint: The endpoint/url to a offline/local LLM, if available (like llama.cpp). In that case, model can be set to None.
        """
        self.model = model
        self.endpoint = local_llm_endpoint
        self.system_role_message = None
        if local_llm_endpoint:
            self.client = OpenAI(
                base_url=local_llm_endpoint, # server started with llama.cpp server
                api_key = "sk-no-key-required"
            )
        return

    def get_direct_response(self, messages, **kwargs):
        """
        Get a response from the LLM API using pre-formatted messages for the LLM API call

        Args:
         messages (List[Dict[str, str]], optional): A pre-formatted list of messages to send to the LLM. 
        Returns:
            str: The content of the LLM's response message.
        Examples:
            ### Using pre-formatted messages
            response = llm_client.get_direct_response(query_text="Hello", messages=[{"role": "user", "content": "Hello"}])
        """
        response = completion(
                    messages=messages,
                    model=self.model,
                    **kwargs
                )
        return response.choices[0].message.content
    
    def get_response(self, query_text, conversation_manager: ConversationManager, include_history=False, **kwargs):
            """
            Get a response from the LLM API using a conversation manager to handle message history and formatting.

            Args:
                query_text (str): The user's input text. Used when conversation_manager is provided.
               
                conversation_manager (ConversationManager): An instance of ConversationManager
                    used to manage the conversation history and system messages. Defaults to None.
                include_history (bool, optional): Whether to include previous conversation history 
                    when using conversation_manager. Ignored if messages is provided. Defaults to False.
                **kwargs: Additional keyword arguments to be passed to the LLM API call.

            Returns:
                str: The content of the LLM's response message.

            Raises:
                OpenAIError: If there's an error during the API call to the LLM when using conversation_manager.

            Note:
                - When using conversation_manager, this method automatically adds the user's query 
                and the LLM's response to the conversation history.
                - The method uses the 'completion' function from litellm for the API call.

            Examples:
                ### Using conversation manager
                conv_manager = ConversationManager()
                response = llm_client.get_response(query_text="Hello", conversation_manager=conv_manager, include_history=True)
            """


            conversation_manager.add_to_history(role="user", content=query_text)
            messages = conversation_manager.get_messages(include_history=include_history)

            print("messages", messages)
            try:
                response = completion(
                    messages=messages,
                    model=self.model,
                    **kwargs
                )

                conversation_manager.add_to_history(role="assistant", content=response.choices[0].message.content)
                return response.choices[0].message.content
            except OpenAIError as e:
                print(e)
                return None
        


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

def get_param_details(self, function):
    """
    Returns the parameters and type description of a function from function signature.
    """
     # Get the signature of the function
    sig = inspect.signature(function)
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
    
    return param_dict, type_descriptions


def extract_json_from_response(response: str):
    # Try to parse the response directly
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Check for the "```json" marker
        if "```json" in response:
            # Split the response to isolate the JSON portion
            # Extract content after the "```json" marker
            json_part = response.split("```json")[-1]
            # Further split to handle the closing "```" and extract only JSON
            json_part = json_part.split("```")[0].strip()
            
            # Try parsing the isolated JSON part
            try:
                return json.loads(json_part)
            except json.JSONDecodeError:
                pass  # If parsing fails, continue to the next method
        
        # If direct parsing fails, use regex to find JSON-like substrings
        json_strings = re.findall(r'\{.*?\}', response, re.DOTALL)
        
        # Loop through found strings and validate JSON
        for json_string in json_strings:
            try:
                # Attempt to load the JSON
                return json.loads(json_string)
            except json.JSONDecodeError:
                continue  # Try the next found string

    # If all attempts fail, return None or raise an error
    return None

def llm_extract_all_parameters(function_name, query_text,llm_client:LLMClient,args_dict=None):
    """
    Extract all parameters for a given function using an LLM and map them to correct kwargs.
    
    Args:
        function_name: The function for which to extract parameters.
        query_text: The input text to analyze for parameter extraction.
        args_dict: A dictionary mapping parameter names to their types/descriptions. If None, the function signature is used.
    Returns:
        A JSON string containing the extracted parameters mapped to their correct kwargs.
    """

    if args_dict is None:
        sig = inspect.signature(function_name)
        param_dict, type_descriptions = get_param_details(function_name)
        prompt_intro = f"""Analyze the following text to extract parameters for the function "{function_name}".
        The function takes the following parameters:
        {json.dumps(param_dict, indent=2)}

        Where each parameter type description is as follows:
            {json.dumps(type_descriptions, indent=2)}"""
    else:
        prompt_intro = f"""Analyze the following text to extract parameters for the function "{function_name}".
        The function takes the following parameters:
        {json.dumps(args_dict, indent=2)}"""

    prompt = f"""
    {prompt_intro}

    Text to analyze:

    "{query_text}"

    """
    system_message = f"""
    You are a helpful assistant that analyzes text to extract parameters for functions. You will be provided with the text, function name and its input parameters.
    Your task is to process the information provided and return the relevant parameter values in a specific JSON format.
    Extract the values for each parameter and only return a JSON object where the keys are the parameter names and the values are the extracted values.
    For List types, provide a list of values.
    For complex types (like Pydantic models), provide a dictionary with the field names as keys.
    If a value for a parameter is not found, omit it from the JSON.
    Strictly return JSON object to ensure correct formatting so that I can directly do json.loads().

    Expected JSON output format:
    {{
        "param_name1": value1,
        "param_name2": [value2a, value2b],
        "param_name3": {{"field1": value3a, "field2": value3b}}
    }}
    """


    # Send prompt to LLM and get the response
    messages = [{ "content": prompt,"role": "user"},
                {"role":"system","content": system_message}]
    llm_response = llm_client.get_direct_response(messages=messages)

    #   Parse the response from the llm
    try:
        extracted_params = extract_json_from_response(llm_response)

        if args_dict is not None:
            return extracted_params
        
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

    messages = [{ "content": prompt,"role": "user"}]
    result = llm_client.get_direct_response(messages=messages)

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
    
    messages = [{ "content": prompt,"role": "user"}]
    llm_response = llm_client.get_direct_response(messages=messages)

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
