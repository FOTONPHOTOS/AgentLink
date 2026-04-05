from llama_cpp import Llama
from llama_cpp.llama_chat_format import Llava15ChatHandler
import os

model_path = "/root/AgentLink/models/llava-v1.5-7b-ocr-pretrain.Q4_K_M.gguf"
mmproj_path = "/root/AgentLink/models/mmproj-model-f16.gguf"

print(" Starting test load...")
chat_handler = Llava15ChatHandler(clip_model_path=mmproj_path)
llm = Llama(
    model_path=model_path,
    chat_handler=chat_handler,
    n_ctx=2048,
    n_threads=2,
    verbose=True
)
print(" Test load successful")
