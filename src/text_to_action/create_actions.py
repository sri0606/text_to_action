from .vector_emb import VectorStore, ModelSource
import time

def create_actions_embeddings(functions_description, save_filename,
                              embedding_model="all-MiniLM-L6-v2",model_source=ModelSource.SBERT):
    """
    Creates embeddings (VectorStore) for the given functions_description and saves it to a file (.h5).
    """
    store = VectorStore(embedding_model=embedding_model,model_source=model_source)
    for i in functions_description:
        store.add_vector(text=i["prompt"],id_name=i["name"])
    store.save(save_filename)

if __name__ == "__main__":
    #sample
    functions_description = [    {
        "name": "add",
        "prompt": "20+50"
    },
    {
        "name": "subtract",
        "prompt": "What is 10 minus 4?"
    }]
    
    start_time = time.time()    
    create_actions_embeddings(functions_description, "calculator.h5")
    print("Time taken to add vectors: ",time.time()-start_time)
    
