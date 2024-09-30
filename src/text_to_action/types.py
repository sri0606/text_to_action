from enum import Enum, auto
from typing import List, Dict, Union,Any
import json
from dataclasses import dataclass

class ModelSource(Enum):
    HUGGINGFACE = auto()
    SBERT = auto()

class LLM_API(Enum):
    OPEN_AI = "open_ai"
    GROQ = "groq"
    
@dataclass
class FunctionArgument:
    type: str
    required: bool

@dataclass
class FunctionDescription:
    description: str
    examples: List[str]
    args: Dict[str, FunctionArgument]

    def validate(self):
        if not isinstance(self.description, str):
            raise ValueError("Description must be a string")
        if not isinstance(self.examples, list) or not all(isinstance(i, str) for i in self.examples):
            raise ValueError("Examples must be a list of strings")
        if not isinstance(self.args, dict):
            raise ValueError("Args must be a dictionary")
        for arg_name, arg_info in self.args.items():
            if not isinstance(arg_info, FunctionArgument):
                raise ValueError(f"Arg {arg_name} must be a FunctionArgument instance")
            if not isinstance(arg_info.type, str):
                raise ValueError(f"Type of {arg_name} must be a string")

def validate_functions(data: Dict[str, Any]) -> List[str]:
    invalid_functions = []
    
    for func_name, func_info in data.items():
        try:
            # Create a FunctionDescription instance from the data
            func_desc = FunctionDescription(
                description=func_info['description'],
                examples=func_info['examples'],
                args={arg_name: FunctionArgument(**arg_info) for arg_name, arg_info in func_info['args'].items()}
            )
            # Validate the function description
            func_desc.validate()
        except Exception as e:
            print(f"Invalid data for function '{func_name}': {e}")
            invalid_functions.append(func_name)

    return invalid_functions

# Example usage
if __name__ == "__main__":
    with open('desc.json', 'r') as file:
        function_desc = json.load(file)
    
    invalid_functions = validate_functions(function_desc)
    if invalid_functions:
        print("Invalid functions:", invalid_functions)
    else:
        print("All functions are valid.")


