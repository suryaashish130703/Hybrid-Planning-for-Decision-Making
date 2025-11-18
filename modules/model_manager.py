import os
import json
import yaml
import requests
import asyncio
import time
import re
from pathlib import Path
from google import genai
from google.genai import errors as genai_errors
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).parent.parent
MODELS_JSON = ROOT / "config" / "models.json"
PROFILE_YAML = ROOT / "config" / "profiles.yaml"

class ModelManager:
    def __init__(self):
        self.config = json.loads(MODELS_JSON.read_text())
        self.profile = yaml.safe_load(PROFILE_YAML.read_text())

        self.text_model_key = self.profile["llm"]["text_generation"]
        self.model_info = self.config["models"][self.text_model_key]
        self.model_type = self.model_info["type"]
        
        # Rate limiting for free tier (15 requests per minute = 4 seconds between calls)
        self.last_call_time = 0
        self.min_interval = 5.0  # 5 seconds = 12 calls per minute (safer margin)

        # ✅ Gemini initialization (your style)
        if self.model_type == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError(
                    "GEMINI_API_KEY environment variable is not set!\n"
                    "Please create a .env file in the project root with:\n"
                    "GEMINI_API_KEY=your_api_key_here\n\n"
                    "Or set it as an environment variable:\n"
                    "export GEMINI_API_KEY=your_api_key_here  # Linux/Mac\n"
                    "set GEMINI_API_KEY=your_api_key_here     # Windows CMD\n"
                    "$env:GEMINI_API_KEY='your_api_key_here'  # Windows PowerShell"
                )
            self.client = genai.Client(api_key=api_key)

    async def generate_text(self, prompt: str) -> str:
        # Rate limiting for Gemini free tier
        if self.model_type == "gemini":
            now = time.time()
            time_since_last_call = now - self.last_call_time
            if time_since_last_call < self.min_interval:
                wait_time = self.min_interval - time_since_last_call
                print(f"⏳ Rate limiting: waiting {wait_time:.1f}s before next API call...")
                await asyncio.sleep(wait_time)
            self.last_call_time = time.time()
            return await self._gemini_generate_with_retry(prompt)

        elif self.model_type == "ollama":
            return self._ollama_generate(prompt)

        raise NotImplementedError(f"Unsupported model type: {self.model_type}")

    async def _gemini_generate_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Generate text with automatic retry on rate limit errors."""
        for attempt in range(max_retries):
            try:
                return self._gemini_generate(prompt)
            except (genai_errors.ClientError, Exception) as e:
                # Check if it's a 429 rate limit error
                is_rate_limit = False
                error_str = str(e)
                
                # Check multiple ways the error might indicate rate limiting
                if hasattr(e, 'status_code') and e.status_code == 429:
                    is_rate_limit = True
                elif '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                    is_rate_limit = True
                
                if is_rate_limit:
                    # Extract retry delay from error message if available
                    retry_delay = 60  # Default: wait 60 seconds
                    
                    # Try to extract the retry delay from the error message
                    match = re.search(r'Please retry in ([\d.]+)s', error_str)
                    if match:
                        retry_delay = float(match.group(1)) + 2  # Add 2s buffer
                    else:
                        # Try alternative patterns
                        match = re.search(r'retry.*?(\d+\.?\d*)\s*seconds?', error_str, re.IGNORECASE)
                        if match:
                            retry_delay = float(match.group(1)) + 2
                    
                    if attempt < max_retries - 1:
                        print(f"⚠️ Rate limit exceeded (429). Waiting {retry_delay:.1f}s before retry {attempt + 1}/{max_retries}...")
                        await asyncio.sleep(retry_delay)
                        # Reset last_call_time to allow immediate retry after wait
                        self.last_call_time = time.time()
                        continue
                    else:
                        raise Exception(
                            f"Rate limit exceeded after {max_retries} retries. "
                            f"Please wait a few minutes and try again, or use a different API key."
                        )
                else:
                    # Not a rate limit error, re-raise
                    raise
        
        raise Exception("Failed to generate text after retries")

    def _gemini_generate(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_info["model"],
            contents=prompt
        )

        # ✅ Safely extract response text
        try:
            return response.text.strip()
        except AttributeError:
            try:
                return response.candidates[0].content.parts[0].text.strip()
            except Exception:
                return str(response)

    def _ollama_generate(self, prompt: str) -> str:
        response = requests.post(
            self.model_info["url"]["generate"],
            json={"model": self.model_info["model"], "prompt": prompt, "stream": False}
        )
        response.raise_for_status()
        return response.json()["response"].strip()
