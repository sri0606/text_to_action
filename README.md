# Text-to-Action

## Overview

Text-to-Action is a system that transaltes natural language commands to programmatic actions. It interprets user input, determines the most appropriate action to execute, extracts relevant parameters, and performs corresponding actions.

You can use this to automate tasks, either within your application or for external use, by letting users give natural language commands. For example, if you're building an image editing app, you can use TextToAction to understand what the user wants (like resizing or cropping an image) and even perform the action automatically.

### How to use

```bash
git clone https://github.com/sri0606/text_to_action.git
or
pip install text-to-action
```

Below is a simple example of how to use TextToAction to handle user input and automatically perform actions like simple calculator operations:

```python
  import os
  from src.text_to_action import TextToAction, LLMClient
  from dotenv import load_dotenv
  load_dotenv()

  llm_client = LLMClient(model="groq/llama3-70b-8192")
  # Get the path to the actions folder
  current_directory = os.path.dirname(os.path.abspath(__file__))
  calculator_actions_folder = os.path.join(current_directory,"src","text_to_action","example_actions","calculator")

  # Initialize TextToAction dispatcher with actions folder and LLM client
  dispatcher = TextToAction(
      actions_folder=calculator_actions_folder, 
      llm_client=llm_client,
      verbose_output=True, 
      application_context="Calculator", 
      filter_input=True
  )

  user_input = input("Enter your query: ") # (mulitply 3,4,5) or (add 3,4 and multiply 3,4)
  results = dispatcher.run(user_input)
  # Example output:
  # {'message': 'Detected multiple actions.', 
  # 'results': [
  #    {'action': 'add', 'args': {'values': [3, 4]}, 'output': 7}, 
  #    {'action': 'multiply', 'args': {'values': [3, 4]}, 'output': 12}
  #   ]
  #}
```

Apart from directly running actions, TextToAction also allows you to extract actions and parameters separately. This can be useful when you want more control over how the system processes user input.

```python
# Extract actions based on the user's query
result1 = dispatcher.extract_actions(query_text="multiply 3,4,5")
# Output: {'actions': ['multiply'], 'message': 'Sure, I can help you with that.'}

# Extract parameters for a specific action (e.g., 'multiply') from the user's query
result2 = dispatcher.extract_parameters(
    query_text="multiply 3,4,5", 
    action_name="multiply", 
    args={"values": {"type": "List[int]", "required": True}}
)
# Output: {'values': [3, 4, 5]}

# Extract both actions and parameters together
result3 = dispatcher.extract_actions_with_args(query_text="multiply 3,4,5")
# Output: {'actions': [{'action': 'multiply', 'args': {'values': [3, 4, 5]}}], 
#          'message': 'Sure I can help you with that. Starting calculation now.'}

```
### Quick Notes:

- Get an API keyfrom services like Groq (free-tier available), OpenAI or any other service [check supported services](https://docs.litellm.ai/docs/providers). Create a `.env` file and set the api keys values (like `GROQ_API_KEY`, `OPENAI_API_KEY`).

- If you are using NER (not recommended) for parameters extraction, download the corresponding model from spacy.

  ```
  python -m spacy download en_core_web_trf
  ```

# Where to start

## Step 1: Describe actions `descriptions.json`

  First, create a json file listing actions descriptions strictly in the following format:

  ```json
  {
      "add": {
          "description": "Add or sum a list of numbers",
          "examples": ["20+50", "add 10, 30, 69", "sum of 1,3,4", "combine numbers", "find the total"],
          "args": {
              "values": {
                  "type": "List[int]",
                  "required": true
              }
          }
      },
      "subtract": {
          "description": "Subtract two numbers",
          "examples": ["10 - 5", "subtract 8 from 20", "what's 50 minus 15?", "deduct 5 from 10"],
          "args": {
              "a": {
                  "type": "int",
                  "required": true
              },
              "b": {
                  "type": "int",
                  "required": true
              }
          }
      }
  }
```
  Better and diverse descriptions for each function, better accuracy.

## Step 2: Create embeddings `embeddings.h5`

  Next, you should create embeddings for actions.

  ```python
  from text_to_action import create_action_embeddings

  # you can use SBERT or other huggingface models to create embeddings
  descriptions_filepath = os.path.join("example_actions", "calculator", "descriptions.json")
  save_to = os.path.join("example_actions", "calculator", "embeddings.h5")

  create_actions_embeddings(descriptions_filepath, save_to=save_to,validate_data=True)
  ```

## Step 3: (Optional) Define actions/functions `implementation.py`

Optionally, define the necessary functions and save them to a file. Infact, you can define the functions in any language you want. You can use TextToAction through a server. Checkout [server.py](server.py)

  ```python
  def add(values: List[int]) -> int:
      """
      Returns the sum of a list of integers.
      """
      return sum(values)

  def subtract(a: int, b: int) -> int:
      """
      Returns the difference between a and b.
      """
      return a - b
  ```

## Use

**Save the `descriptions.json`, `embeddings.h5` and `implementations.py` (optional) to a single folder.**

```python
from text_to_action import TextToAction
from dotenv import load_dotenv
load_dotenv()

# use the same embedding model, model source you used when creating the actions embeddings
dispatcher = TextToAction(actions_folder = calculator_actions_folder, llm_client=llm_client,
                            verbose_output=True,application_context="Calculator", filter_input=True)

```

## Key Components

1. **Text to Action**: The core component that orchestrates the flow from query to action execution.

2. **Vector Store**: Stores embeddings of function descriptions and associated metadata for efficient similarity search.

3. **Parameter Extractor**: Extracts function arguments from the input text using NER or LLM-based approaches.

## How it works

1. The system receives a natural language query from the user.
2. The query is processed by the Vector Store to identify the most relevant function(s).
3. The Parameter Extractor analyzes the query to extract required function arguments.
4. The Action Dispatcher selects the most appropriate function based on similarity scores and parameter availability.
5. The selected function is executed with the extracted parameters.
6. The result is returned to the user.

## Possible use Cases

- Natural Language Interfaces for APIs
- Chatbots and Virtual Assistants
- Automated Task Execution Systems
- Voice-Controlled Applications

## Contributions

Contributions are welcome.
