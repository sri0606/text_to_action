import os
from src.text_to_action import TextToAction, LLMClient

if __name__ == '__main__':

    llm_client = LLMClient(model="groq/mixtral-8x7b-32768")
    # Get the directory of the current file
    current_directory = os.path.dirname(os.path.abspath(__file__))
    calculator_actions_folder = os.path.join(current_directory,"src","text_to_action","example_actions","calculator")

    dispatcher = TextToAction(actions_folder = calculator_actions_folder, llm_client=llm_client,
                            verbose_output=True,application_context="Calculator", filter_input=True)

    while True:
        user_input = input("Enter your query: ")
        if user_input.lower() == 'quit':
            break
        results = dispatcher.run(user_input)
        print(results)
        print('\n')