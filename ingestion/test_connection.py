from dotenv import load_dotenv
import os

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

print("APP_ID:", APP_ID)
print("APP_KEY:", APP_KEY)