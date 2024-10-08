from abc import ABC, abstractmethod
from typing import Dict, Any, List
from .utils import verbose_print
import inspect
from collections import Counter
from pydantic import BaseModel
from .llm_utils import llm_extract_parameters, llm_map_pydantic_parameters,llm_extract_all_parameters,LLMClient
from .entity_models import *

class ParameterExtractor(ABC):
    def __init__(self,llm_client: LLMClient):
        self.llm_client = llm_client

    @abstractmethod
    def extract_parameters(self, query_text: str, function_name: Union[callable,str]) -> Dict[str, Any]:

        pass

    def clear(self):
        return

class NERParameterExtractor(ParameterExtractor):
    
    def __init__(self, spacy_model_ner: str,llm_client: LLMClient):
        import spacy
        self.entity_recognizer = spacy.load(spacy_model_ner)
        self.entities = None
        super().__init__(llm_client)

    def clear(self):
        self.entities = None
        return 
    
    def _ner(self, query_text: str) -> Dict[str, List[str]]:
        doc = self.entity_recognizer(query_text)
        self.entities = {}
        for ent in doc.ents:
            entity_type = str(ent.label_).upper()
            value = ent.text
            if entity_type in globals():
                class_obj = globals()[entity_type]
                if issubclass(class_obj, BaseModel):
                    fields = list(class_obj.model_fields.keys())
                    if len(fields) == 1:
                        instance = class_obj(**{fields[0]: value})
                    else:
                        instance = class_obj(value)
                    self.entities[entity_type] = [instance] if entity_type not in self.entities else self.entities[entity_type] + [instance]
    
    def extract_parameters(self, query_text: str, function_name: Union[callable,str]) -> Dict[str, Any]:
        """
        Return extracted args from the query text using NER (and LLM if any params are missing).
        """
        if self.entities is None:
            self._ner(query_text)
        
        return self._map_parameters(function_name, self.entities, query_text)

    def _map_parameters(self, function_name: callable, extracted_parameters, query_text: str) -> Dict[str, Any]:
        # Get the signature of the function
        sig = inspect.signature(function_name)
        
        # Prepare a dictionary to hold the parameter instances/values
        arguments = {}
        
       # Count the expected number of parameters for each type
        expected_param_counts = Counter(param.annotation for param in sig.parameters.values())

        # Check if we need to extract additional parameters
        for param_annotation, expected_count in expected_param_counts.items():
            param_type = param_annotation.__name__.upper()
            if param_type == "LIST":
                param_type =  param_annotation.__args__[0].__name__.upper()

            if param_type not in extracted_parameters:
                extracted_parameters[param_type] = []
            
            if len(extracted_parameters[param_type]) < expected_count and param_type != 'STR':
                # Use LLM to extract missing parameters
                verbose_print(f"Extracting parameters for {param_type} using llm: {extracted_parameters[param_type]}")
                extracted_parameters[param_type] = llm_extract_parameters(query_text, globals()[param_type],self.llm_client)
        

        verbose_print(f"Extracted paramaeters: {extracted_parameters}")
        # Check if we can skip llm_map_pydantic_parameters
        need_llm_mapping = False
        for name, param in sig.parameters.items():
            if param.annotation is str:
                arguments[name] = query_text

            elif param.annotation.__name__ == 'List':
                param_type = param.annotation.__args__[0].__name__.upper()
                if param_type in extracted_parameters:
                    arguments[name] = extracted_parameters[param_type]
                else:
                    print(f"No matching entity found for {name}")
                    return None
                
            elif param.annotation.__name__.upper() in extracted_parameters:
                extracted_values = extracted_parameters[param.annotation.__name__.upper()]
                if len(extracted_values) == 1:
                    arguments[name] = extracted_values[0]
                else:
                    need_llm_mapping = True
                    break

            else:
                print(f"No matching entity found for {name}")
                return None

        if need_llm_mapping:
            # We need to use llm_map_pydantic_parameters
            verbose_print(f"Mapping parameters to correct kwarg using llm: {extracted_parameters}")
            param_descriptions = ", ".join([f"{name} ({param.annotation.__name__})" for name, param in sig.parameters.items()])
            mapped_params = llm_map_pydantic_parameters(text=query_text,function_name= function_name.__name__, 
                                                        param_descriptions=param_descriptions, extracted_parameters=extracted_parameters, 
                                                        llm_client=self.llm_client)

            verbose_print(f"param  mapping: {mapped_params}")
            for name, param in sig.parameters.items():
                if name in mapped_params:
                    arguments[name] = mapped_params[name]
                elif param.annotation is str:
                    arguments[name] = query_text
                else:
                    print(f"No matching entity found for {name}")
                    return None

        return arguments
    
class LLMParameterExtractor(ParameterExtractor):

    def extract_parameters(self, query_text: str, function_name: Union[callable,str],arguments_dict:Dict[str,Dict[str,Any]]=None) -> Dict[str, Any]:
        """
        Extract all parameters for a given function using an LLM and map them to correct kwargs.
    
        Args:
            function_name: The function for which to extract parameters.
            query_text: The input text to analyze for parameter extraction.
            args_dict: A dictionary mapping parameter names to their types/descriptions. If None, the function signature is used.
        Returns:
            A JSON string containing the extracted parameters mapped to their correct kwargs.
        """
        return llm_extract_all_parameters(function_name=function_name, query_text=query_text,
                                          llm_client=self.llm_client,args_dict=arguments_dict)
