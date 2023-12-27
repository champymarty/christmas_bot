import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

DATA_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), "members.bin")