import importlib.util
from pathlib import Path
import sys
from typing import Any, Dict
from .vector_emb import VectorStore, ModelSource
from .entity_models import *
from .utils import verbose_print,Config
from .extract_parameters import NERParameterExtractor,LLMParameterExtractor
from .llm_utils import LLMClient,LLM_API

def load_module_from_path(file_path:str):
    file_path = Path(file_path)
    module_name = file_path.stem  # Use the file name without extension as the module name
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

class ActionDispatcher:
    """
    Function Calling mechanism.
    """
    def __init__(self,action_embedding_filename,actions_filepath,
                 llm_api = LLM_API.GROQ, llm_model = "llama3-70b-8192",
                 use_llm_extract_parameters=False,
                 spacy_model_ner="en_core_web_trf",embedding_model="all-MiniLM-L6-v2",model_source = ModelSource.SBERT,
                 verbose_output=False):
        """
        Parameters:
        action_embedding_filename : The path to the vector store. All embedding files are located in /action_embeddings dir (Example: calculator.h5)
        actions_filepath : The path to the py file where functions/actions are defined.
        llm_api : The LLM API to use. (Default: LLM_API.GROQ)
        llm_model : The LLM model to use. (Default: llama3-70b-8192)
        use_llm_extract_parameters : Whether to use LLM to extract all parameters. (Default: False)
        spacy_model_ner : The name of the spaCy model to use for parameter extraction. (Default: en_core_web_trf)
        embedding_model : The identifier of the embedding model to use. Makse sure it's the same model that is used when creating embeddings. (Default: all-MiniLM-L6-v2)
        model_source : The source of the embedding model. (Default: ModelSource.SBERT)
        """
        self.embeddings_store = VectorStore(embedding_model=embedding_model,
                                                      model_source =model_source)
        self.embeddings_store.load(action_embedding_filename)
        self.llm_client = LLMClient(llm_api,llm_model)
        self.parameter_extractor = LLMParameterExtractor(self.llm_client) if use_llm_extract_parameters else NERParameterExtractor(spacy_model_ner,self.llm_client)

        self.actions_module = load_module_from_path(actions_filepath)
        
        Config.set_verbose(verbose_output)

    @staticmethod
    def execute_action(function_name: callable, extracted_parameters: Dict[str, Any]) -> Any:
        verbose_print("Executing action: {}".format(function_name.__name__))
        try:
            result = function_name(**extracted_parameters)
            return result
        except Exception as e:
            print(f"Error executing function: {e}")
            return None
        
    def dispatch(self, query_text,*args, **kwargs):
        """
        Dispatch the task to the appropriate functions.

        Args:
            text : The text input.

        Returns: results : The results of the function calls.
        """
        possible_actions = self.embeddings_store.query(query_text,k=5)

        self.parameter_extractor.clear()

        results = {}
        threshold = 0.45
        # threshold value for function selection
        if "threshold" in kwargs:
            threshold = kwargs["threshold"]     

        for action in possible_actions:
            if action[1] > threshold and action[0].id_name not in results:
                action_to_perform = getattr(self.actions_module, action[0].id_name)
                try:
                    extracted_params = self.parameter_extractor.extract_parameters(query_text, action_to_perform)
                except Exception as e:
                    print(f"Error extracting parameters for function {action_to_perform.__name__}: {e}")
                    continue
                results[action[0].id_name] = self.execute_action(action_to_perform, extracted_params)
                break

        return results
        

if __name__ == '__main__':

    dispatcher = ActionDispatcher("calculator.h5","calculator",use_llm_extract_parameters=True)
    Config.set_verbose(True)
    while True:
        user_input = input("Enter your query: ")
        if user_input.lower() == 'quit':
            break
        results = dispatcher.dispatch(user_input)
        for result in results:
            print(result,":",results[result])
        print('\n')