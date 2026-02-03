import os
import asyncio
from groq import Groq
from deepeval.models.base_model import DeepEvalBaseLLM

class GroqJudge(DeepEvalBaseLLM):
    def __init__(self, model="llama-3.3-70b-versatile"):
        self.model = model
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def load_model(self):
        return self.client

    def generate(self, prompt: str) -> str:
        chat_completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model,
        )
        return chat_completion.choices[0].message.content

    async def a_generate(self, prompt: str) -> str:
        return self.generate(prompt)

    def get_model_name(self):
        return "Groq Llama-3.3-70b-versatile"