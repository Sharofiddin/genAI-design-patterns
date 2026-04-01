MODEL_ID='CohereLabs/tiny-aya-global'
import os
from dotenv import load_dotenv
load_dotenv("keys.env")
assert os.environ["HF_TOKEN"].startswith("hf"),\
       "Please sign up for access to the specific Llama model via HuggingFace and provide access token in keys.env file"

from transformers import pipeline

pipe = pipeline(
    task="text-generation", 
    model=MODEL_ID,
    use_fast=True,
    kwargs={
        "return_full_text": False,
    },
    model_kwargs={}
)