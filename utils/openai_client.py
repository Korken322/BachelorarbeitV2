from openai import OpenAI
from dotenv import load_dotenv
import os

# Laden der Umgebungsvariablen
load_dotenv()

# OpenAI-Client initialisieren
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_openai_client():
    return client


