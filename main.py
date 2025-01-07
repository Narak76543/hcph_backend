from fastapi import FastAPI

# For using in every module
app = FastAPI()

# Import all modules here
from api.register import *