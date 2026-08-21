from dotenv import load_dotenv
from google import genai
from google.genai import types
import os
import json
load_dotenv()
api_key=os.getenv("gemini_api_key")
class Prompt:
    def __init__(self,detail:dict):
        self.gem_obj=genai.Client(api_key=api_key)
    def generate(self,detail:dict):
        self.prompt=f"{detail} these are the details of a mail, now give me the summary and a reply draft for this mail in json format and return nothing except json"
        response=self.gem_obj.models.generate_content(model="gemini-3-flash-preview",contents=self.prompt, config=types.GenerateContentConfig(response_mime_type="application/json"))
        out=response.text
        self.result=json.loads(out)