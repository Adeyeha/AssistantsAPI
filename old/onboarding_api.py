# Import necessary libraries
from openai import OpenAI
import requests
import time
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, HTTPException, File, UploadFile
import os
from pydantic import BaseModel, Field
from typing import Annotated, Union
from fastapi import Body, FastAPI
from pydantic import BaseModel

# Models
class Thread(BaseModel):
    id: str = Field(description="User message thread. To manage messages per user.", examples=["myai-1234-xyz"])

class Message(BaseModel):
    username: str = Field(description="User's username.")
    age: int = Field(gt=0, description="User's age.")
    gender: str = Field(description="User's gender.")
    country: str = Field(description="User's country.")
    thread_id: Thread = Field(description="ID of the message thread to manage messages per user.")
    user_prompt: str = Field(description="User's message prompt.")

class MessageCompletion(BaseModel):
    completion: str = Field(description="AI response to User Prompt.", examples=["The capital of USA is Washington"])

class UploadedFile(BaseModel):
    id: str = Field(description="File ID of uploaded File", examples=["myai-1234-xyz"])


app = FastAPI()

load_dotenv()

# Load API key from environment variable
api_key = os.getenv('API_KEY')

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

async def is_authenticated(api_key_header: str = Security(api_key_header)):
    if not api_key_header == os.getenv("API_KEY"):
        raise HTTPException(
            status_code=401, 
            detail="Incorrect Authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
        return True   

# Initialize OpenAI client with API key
openai_client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

# Set OpenAI Assistant ID
assistant_id = os.getenv('ASSISTANT_ID')

# Building blocks
def create_openai_file(file_bytes, purpose="assistants"):
    # Create a file in OpenAI and return its ID
    response = openai_client.files.create(file=file_bytes, purpose=purpose)
    return response.id

def create_openai_assistant_file(file_id):
    # Create an assistant file in OpenAI and return the created file
    assistant_file = openai_client.beta.assistants.files.create(
        assistant_id=assistant_id,
        file_id=file_id
    )
    return assistant_file

def update_openai_assistant(file_ids):
    # Update the OpenAI Assistant with specified file IDs
    myai = openai_client.beta.assistants.update(
        assistant_id,
        tools=[{"type": "retrieval"}],
        file_ids=file_ids,
    )
    return myai

def create_message_on_openai_assistant(thread_id, user_prompt):
    # Create a user message in the specified thread
    thread_message = openai_client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=user_prompt
    )
    return thread_message

def process_message_on_openai_assistant(thread_id, username, age, gender, country):
    # Process a message in the specified thread and return the run
    run = openai_client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions=f"""You are a multi-lingual, delightful and witty onboarding assistant for MyAI app. 
        You are funny and full of personality. You are to guide users through a step-by-step onboarding process on the app, one step at a time, 
        and also answer questions relating to the app. MyAI is a personal assistant app. You are MyAI. 
        The details you need are in the knowledge provided in the files. Only answer questions relating to the app.
        You are responding to {username}, a {age} years old {gender} {country} national.
        """
    )
    return run 

def check_message_processing_status_on_openai_assistant(run, thread_id):
    # Check the status of message processing and wait until it's completed
    while run.status != 'completed':
        time.sleep(1)
        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    return run

def retrieve_message_response_on_openai_assistant(run, thread_id):
    # Retrieve the assistant's messages from the specified thread and run
    messages = openai_client.beta.threads.messages.list(
        thread_id=thread_id
    )
    return [message.content[0].text.value for message in messages if message.run_id == run.id and message.role == "assistant"][0]


@app.post("/create-thread", status_code=201, response_model=Thread)
async def create_openai_assistant_thread(
    auth: bool = Depends(is_authenticated)
):
    try:
        thread_id = create_openai_assistant_thread()
        return Thread(id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/message", status_code=201, response_model=MessageCompletion)
async def send_message_and_get_response(
    message: Annotated[
        Message,
        Body(
            examples=[
                {
                    "username": "Foo",
                    "age": 25,
                    "gender": "male",
                    "country": "England",
                    "thread_id": "<<input valid thread id>>",
                    "user_prompt": "What is the capital of my country?"
                }
            ],
        ),
    ],     
    auth: bool = Depends(is_authenticated),
    
):
    try:
        message = create_message_on_openai_assistant(message.thread_id, message.user_prompt)
        run = process_message_on_openai_assistant(message.thread_id, message.username, message.age, message.gender, message.country)
        run = await check_message_processing_status_on_openai_assistant(run, message.thread_id)
        response_message = retrieve_message_response_on_openai_assistant(run, message.thread_id)
        return MessageCompletion(completion=response_message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/refresh-assistant", status_code=201, response_model=UploadedFile)
async def refresh_openai_assistant_file(
    file: UploadFile,
    auth: bool = Depends(is_authenticated),
):
    try:
        file_id = refresh_openai_assistant_file(file.read())
        return UploadedFile(id= file_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
