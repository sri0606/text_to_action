import os
# Construct the path to the action_embeddings directory
EMBEDDINGS_DIR = os.path.join(os.path.dirname(__file__), "action_embeddings")
ACTIONS_DIR = os.path.join(os.path.dirname(__file__), "actions")
from .action_dispatcher import ActionDispatcher
