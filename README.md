# Text-to-Action Architecture

## Overview

Text-to-Action is a system that transaltes natural language queries to programmatic actions. It interprets user input, determines the most appropriate function to execute, extracts relevant parameters, and performs the corresponding action.

## QuickStart

```python
pip install text-to-action
```

Below is a simple example:

```python
from text_to_action import ActionDispatcher
from dotenv import load_dotenv
load_dotenv()

action_file = "text_to_action/src/text_to_action/actions/calculator.py"
dispatcher = ActionDispatcher(action_embedding_filename="calculator.h5",actions_filepath=action_file,
                                use_llm_extract_parameters=True,verbose_output=True)

while True:
    user_input = input("Enter your query: ") # sum of 3, 4 and 5
    if user_input.lower() == 'quit':
        break
    results = dispatcher.dispatch(user_input)
    for result in results:
        print(result,":",results[result])
    print('\n')
```

### Quick Notes:

- Get an API keyfrom services like Groq (free-tier available) or OpenAI. Create a `.env` file and set the api keys values to either `GROQ_API_KEY` or `OPENAI_API_KEY`.

- If you are using NER for parameters extraction, download the corresponding model from spacy.

  ```
  python -m spacy download en_core_web_trf
  ```

## Creating actions

- First, create a list of actions descriptions in the following format:

  ```python
  functions_description = [    {
          "name": "add",
          "prompt": "20+50"
      },
      {
          "name": "subtract",
          "prompt": "What is 10 minus 4?"
      }]
  ```

  Better and diverse descriptions for each function, better accuracy.

- Then, you can create embeddings for functions using the following:

  ```python
  from text_to_action import create_action_embeddings
  from text_to_action.types import ModelSource

  # you can use SBERT or other huggingface models to create embeddings
  create_actions_embeddings(functions_description, save_filename="calculator.h5",
                              embedding_model="all-MiniLM-L6-v2",model_source=ModelSource.SBERT)
  ```

- Finally, define the necessary functions and save them to a file. Use the types defined in [entity_models](src/text_to_action/entity_models.py) for function parameter types, or create additional types as needed for data validation and to ensure type safety and clarity in your code.

  ```python
  from typing import List
  from text_to_action.entity_models import CARDINAL

  def add(items:List[CARDINAL]):
      """
      Returns the sum of a and b.
      """
      return sum([int(item.value) for item in items])

  def subtract(a: CARDINAL, b: CARDINAL):
      """
      Returns the difference between a and b.
      """
      return a.value - b.value
  ```

You can tehn use created actions:

```python
from text_to_action import ActionDispatcher
from dotenv import load_dotenv
load_dotenv()

# use the same embedding model, model source you used when creating the actions embeddings
# actions_filepath is where the functions are defined
dispatcher = ActionDispatcher(action_embedding_filename="calculator.h5",actions_filepath=action_file,
                                use_llm_extract_parameters=False,verbose_output=True,
                                embedding_model: str = "all-MiniLM-L6-v2",
                                model_source: ModelSource = ModelSource.SBERT,)

```

## Key Components

1. **Action Dispatcher**: The core component that orchestrates the flow from query to action execution.

2. **Vector Store**: Stores embeddings of function descriptions and associated metadata for efficient similarity search.

3. **Parameter Extractor**: Extracts function arguments from the input text using NER or LLM-based approaches.

## Workflow

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

## Future Enhancements

- Integration with more advanced LLMs for improved parameter extraction
- Support for multi-step actions and complex workflows
- User feedback loop for continuous improvement of function matching
- GUI for easy management of the function database

## Contributions

Contributions are welcome.
