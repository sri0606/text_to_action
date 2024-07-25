from src.text_to_action import ActionDispatcher

if __name__ == '__main__':

    action_file = "src/text_to_action/actions/calculator.py"
    dispatcher = ActionDispatcher(action_embedding_filename="calculator.h5",actions_filepath=action_file,
                                  use_llm_extract_parameters=True,verbose_output=True)

    while True:
        user_input = input("Enter your query: ")
        if user_input.lower() == 'quit':
            break
        results = dispatcher.dispatch(user_input)
        for result in results:
            print(result,":",results[result])
        print('\n')