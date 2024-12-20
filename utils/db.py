import mysql.connector
from dotenv import load_dotenv
import os

# Laden der Umgebungsvariablen
load_dotenv()

def connect_to_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv('DB_PASSWORD', 'bachelorarbeit'),
        database="werbetext_generator"
    )
