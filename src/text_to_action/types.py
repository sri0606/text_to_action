from enum import Enum, auto

class ModelSource(Enum):
    HUGGINGFACE = auto()
    SBERT = auto()

class LLM_API(Enum):
    OPEN_AI = "open_ai"
    GROQ = "groq"

