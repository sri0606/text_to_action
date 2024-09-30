import importlib.util
from pathlib import Path
import sys
import os
import json
from typing import Any, Dict, Union, List, Tuple
from .vector_emb import VectorStore, ModelSource
from .entity_models import *
from .utils import verbose_print,Config
from .extract_parameters import NERParameterExtractor,LLMParameterExtractor
from .llm_utils import LLMClient, extract_json_from_response

def load_module_from_path(file_path:str):
    file_path = Path(file_path)
    module_name = file_path.stem  # Use the file name without extension as the module name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

class TextToAction:
    """
    Function Calling mechanism. Detects actions from natural text.
    """
    def __init__(self,
                llm_client: LLMClient,
                actions_folder=None,
                action_embeddings_filepath=None,
                action_descriptions_filepath: Dict[str, Dict[str, Any]] = None,
                action_implementation_filepath=None,
                use_llm_extract_parameters=True,
                application_context="",
                filter_input: bool = False,
                spacy_model_ner="en_core_web_trf",
                embedding_model="all-MiniLM-L6-v2",
                model_source=ModelSource.SBERT,
                verbose_output=False):
        """
        Initializes the class for Text-to-Action functionality.

        Parameters:
            llm_client (LLMClient): The LLM client to interact with for text analysis and understanding.
            actions_folder (str): Path to the folder where `descriptions.json`, `embeddings.h5`, and optionally `implementation.py` are located.
                                If not specified, `action_embeddings_filepath` and `action_descriptions_filepath` must be provided separately.
            action_embeddings_filepath (str): Path to the file that contains action embeddings (e.g., `calculator.h5`). Default is None.
            action_descriptions_filepath (Dict[str, Dict[str, Any]]): Path to the file containing action descriptions (e.g., `descriptions.json`). Default is None.
            action_implementation_filepath (str): Path to the Python file where actions are implemented. If not provided, execution is skipped, and only functions and parameters are extracted.
            use_llm_extract_parameters (bool): Set to True to use the LLM for parameter extraction; otherwise, use spaCy's NER model. For optimal performance, set this to True. Default is True.
            application_context (str): A concise description of the application's domain, such as "Video Editing" or "Calculator", to help the LLM generate relevant results.
            filter_input (bool): If True, filters the input text to detect any actions. If actions are found, it returns them in the order they should be executed. If no actions are found, a relevant message is returned. This may sometimes be unreliable. Default is False.
            spacy_model_ner (str): Name of the spaCy model to use for Named Entity Recognition (NER) during parameter extraction. Default is "en_core_web_trf".
            embedding_model (str): Identifier for the embedding model to use. Ensure it matches the model used for creating embeddings (Default: "all-MiniLM-L6-v2").
            model_source (ModelSource): Source of the embedding model. Default is `ModelSource.SBERT`.
            verbose_output (bool): If True, additional details and messages will be printed for debugging and verbosity. Default is False.

        """

        self.embeddings_store = VectorStore(embedding_model=embedding_model,
                                                      model_source =model_source)
        self.llm_client = llm_client
        self.parameter_extractor = LLMParameterExtractor(llm_client) if use_llm_extract_parameters else NERParameterExtractor(spacy_model_ner,llm_client)

        if actions_folder:
            action_embeddings_filepath, action_descriptions_filepath, action_implementation_filepath = self.validate_file_paths(actions_folder)

        self.embeddings_store.load(action_embeddings_filepath)
        self.actions_module = load_module_from_path(action_implementation_filepath) if action_implementation_filepath is not None else None

        with open(action_descriptions_filepath, 'r') as f:
            self.args_template = json.load(f)
        self.application_context = application_context
        self.filter_input = filter_input
        Config.set_verbose(verbose_output)

    @staticmethod
    def validate_file_paths(actions_folder):
        if actions_folder:
            action_embeddings_filepath = os.path.join(actions_folder, "embeddings.h5")
            action_descriptions_filepath = os.path.join(actions_folder, "descriptions.json")
            actions_filepath = os.path.join(actions_folder, "implementation.py")

            # Check if the first two files exist
            if not os.path.isfile(action_embeddings_filepath):
                raise FileNotFoundError(f"Required embeddings file not found: {action_embeddings_filepath}")
            
            if not os.path.isfile(action_descriptions_filepath):
                raise FileNotFoundError(f"Required functions descriptions file not found: {action_descriptions_filepath}")
            
            # Check if the actions file exists; if not, set it to None
            if not os.path.isfile(actions_filepath):
                actions_filepath = None
            
            return action_embeddings_filepath, action_descriptions_filepath, actions_filepath

    def filter_user_query(self,query_text):
        """
        Filters user query for better results.

        Returns a dictionary
        """
        system_message = "You are an assistant for a Text to Action software. You will receive various user inputs about performing different "+ self.application_context + """ tasks. Please strictly follow these instructions to handle them:
            Output format:
                Strictly return only a JSON response with only "actions" and "message" fields.

            If the input is a unrelated message (e.g., "Hi", "How are you?", "What's up?"), respond politely and return the following JSON:

            {
            "actions": [],
            "message": <General message or greeting>
            }

            But if the input contains a task or action:

            Refine the input by removing irrelevant parts.
            For multiple tasks or actions (e.g., "Hello there. Can you resize the image to 300x300 and send it via email?"), break them down into individual tasks.
            Pass the refined input to the text-to-action software.

            Return a JSON response with the actions.
            Output Structure:

            If no actions are found:

            {
            "actions": [],
            "message": <Sorry I cannot perform that action as of now!>
            }

            If actions/functions are found:

            {
                "actions": [action1_description, action2_description],
                message: "<relevant message>"
            }
            Examples:

            Input: "Hi"
            Output:
            {
            "actions": [],
            "message": hello
            }

            Input: "Hi!. Can you resize the image to 300x300?"
            Output:
            {
            "actions": ["resize image to 300x300" ],
            "message": "Hello there. Sure I can help you with that."
            }

            Input: "Can you resize the image to 300x300 and add brightness?"
            Output:
            {
            "actions": ["resize image to 300x300", "increase brightness"],
            "message": "Detected multiple actions."
            }
        """

        # response_format= { "type": "json_schema", "json_schema": {"actions":'List',"message":str} , "strict": True }
        response = self.llm_client.get_direct_response(messages=[{"role":"system","content":system_message},{"role":"user","content":query_text}])
        format_response = extract_json_from_response(response)
        verbose_print("Filtered query:", format_response)
        return format_response
    
    def execute_action(self,action_name: Union[callable, str], extracted_parameters: Dict[str, Any]) -> Any:
        
        if self.actions_module is None:
            raise Exception("Actions module is not loaded. Please make sure to provide a value for actions_filepath")
        if isinstance(action_name,str):
            action_name = getattr(self.actions_module,action_name)

        verbose_print("Executing action: {}".format(action_name.__name__))

        try:
            result = action_name(**extracted_parameters)
            return result
        except Exception as e:
            print(f"Error executing action: {e}")
            return None
    
    def extract_actions(self, query_text, top_k=1, threshold=0.45)-> Dict[str,Any]:
        """
        Get top matched actions.
        **This doesnt actually execute the action. It just returns the list of top ranked action.**

        Args:
            query_text : The text input.
            top_k : The number of top-ranked actions to consider. (Default: 1)
            threshold : The threshold value for action selection. (Default: 0.45)

         Returns:
            Dict[str, Any]: A dictionary containing:
                - "actions" (List[str]): A list of actions
                - "message" (str): A message describing the status of the action extraction.
        """
        possible_actions = []
        actions = []
        message = ""

        if len(query_text.strip())==0:
            return {"actions": actions, "message": "Empty text cannot be processed."}

        if self.filter_input:
            response = self.filter_user_query(query_text)
            if response is None:
                possible_actions.extend(self.embeddings_store.query(query_text, k=top_k))
            elif len(response["actions"])==0:
                return response
            else:
                for query in response["actions"]:
                    possible_actions.extend(self.embeddings_store.query(query, k=top_k))
        else:
            possible_actions.extend(self.embeddings_store.query(query_text, k=top_k))

        
        for action in possible_actions:
            if action[1] > threshold and action[0].id_name not in actions:
                actions.append(action[0].id_name)

        if self.filter_input and response is not None:
            message = response["message"]
        else:
            message = "Actions detected." if len(possible_actions) > 0 else "Sorry I cannot help you with that. No actions were detected."

        return {"actions": actions, "message": message}

    def extract_parameters(self, query_text, action_name, args=None)->Dict[str,Any]:
        """
        Get the parameters for the action/actions to be called.

        Args:
            query_text : The text input.
            action_name : A dictionary containing the action/function name and its arguments with descriptions
            args : A dictionary containing the arguments description. Defaults to None. If none, will be loaded from action_descriptions json file.
                {
                <arg_name>: {"type": "int", "required": True}
                }
            .
        Returns: results : The extracted parameters for the function.
        """
        
        if args or self.args_template.get(action_name):
            self.parameter_extractor.clear()

            # Extract the arguments for the specified function
            if not args:
                args = self.args_template[action_name]["args"]

            # Create the formatted string
            formatted_args = {key: value['type'] for key, value in args.items()}
            results = self.parameter_extractor.extract_parameters(query_text=query_text, 
                                                                        function_name=action_name,
                                                                        arguments_dict={action_name:formatted_args})
            return results
        else:
            return {}

    
    def extract_actions_with_args(self, query_text: str, top_k: int = 3, threshold: float = 0.45) -> Dict[str, Any]:
        """
        Extract and rank the most relevant actions based on the user's query along with respective args.

        Args:
            query_text (str): The natural language query provided by the user to extract actions from.
            top_k (int, optional): The maximum number of top-ranked actions to consider. Default is 3.
            threshold (float, optional): The minimum similarity threshold for actions to be selected. Actions below this score will be ignored. Default is 0.45.

        Returns:
            Dict[str, Any]: A dictionary containing:
                - "actions" (List[Dict[str, Any]]): A list of action dictionaries, where each action contains:
                    - "action" (str): The name of the function to be executed.
                    - "args" (Dict[str, Any]): The arguments required for the function.
                - "message" (str): A message describing the status of the action extraction.
        """

        actions_extracted = self.extract_actions(query_text=query_text, top_k=top_k, threshold=threshold)
        extracted_functions_args = []
        for function in actions_extracted["actions"]:
            if function in self.args_template:
                # Extract parameters
                extracted_params = self.extract_parameters(
                    query_text=query_text,
                    action_name=function
                )
                
                for param, param_type in self.args_template[function]["args"].items():
                    if param not in extracted_params and not param_type["required"]:
                        extracted_params[param] = None
                    elif param not in extracted_params and param_type["required"]:
                        verbose_print(f"Some or many of required parameters are not found for function {function}. Extracted parameters: {extracted_params}")
                        break
                else:
                    extracted_functions_args.append({
                                "action": function,
                                "args": extracted_params
                            })
        if self.filter_input:
            message = actions_extracted["message"]
        else:
            message = "Actions detected." if len(extracted_functions_args) > 0 else "Sorry I cannot help you with that. No actions were detected."

        return {"actions":extracted_functions_args, "message":message}
    
    def run(self, query_text: str, top_k: int = 1, **kwargs) -> Dict[str, Any]:
        """
        Detects actions from the user's query text and executes them.

        Args:
            query_text (str): The input text from which actions will be extracted and executed.
            top_k (int, optional): The number of top-ranked actions to consider for execution. Defaults to 1.
            **kwargs: Additional parameters to refine the action extraction process (e.g., thresholds, filters).

        Returns:
            Dict[str, Any]: A dictionary containing a message and a list of executed actions with their results.
            The structure of the return value is as follows:
            {
                "message": str,                # An optional message returned by the action extraction process.
                "results": [                   # A list of executed actions with their corresponding arguments and results.
                    {
                        "action": str,          # The name of the executed function.
                        "args": Dict[str, Any], # The arguments passed to the function.
                        "output": Any # The result returned from the function execution.
                    }
                ]
            }

        Raises:
            Exception: If the actions module is not loaded, an exception is raised.

        Example Usage:
            query_text = "Resize the image to 300x300"
            results = run(query_text=query_text, top_k=2)
            # Example of a returned result:
            # {
            #   "message": "Actions extracted successfully.",
            #   "results": [
            #       {
            #           "action": "resize_image",
            #           "args": {"width": 300, "height": 300},
            #           "output": "success"
            #       }
            #   ]
            # }
        """
        if self.actions_module is None:
            raise Exception("Actions module is not loaded. Please make sure to provide a value for action_implementation_filepath.")
        
        actions_to_execute = self.extract_actions_with_args(query_text, top_k, **kwargs)
        results = []
        for action in actions_to_execute["actions"]:
            result = self.execute_action(action_name=action["action"], extracted_parameters=action["args"])
            results.append({
                "action": action["action"],
                "args": action["args"],
                "output": result
            })

        return {"message": actions_to_execute["message"], "results": results}


        