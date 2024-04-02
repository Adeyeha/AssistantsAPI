from fastapi import FastAPI, Depends, HTTPException, Body, UploadFile, Security, File
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Annotated, Union, List, Dict
import time
import os
# from dotenv import load_dotenv
from openai import OpenAI
import json


###################################################### GENERAL CONFIG ###########################################################
# load_dotenv()


# FastAPI app initialization
app = FastAPI()

origins = [
    "http://localhost",
    "http://maya-ai.azurewebsites.net"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Load API key from environment variable
api_key = os.getenv('API_KEY')
api_key_header = APIKeyHeader(name="Authorization", auto_error=False)

# Initialize OpenAI client with API key
openai_client = OpenAI(api_key=os.getenv('OPENAI_KEY'))

# Set OpenAI Assistant ID
onboarding_assistant_id = os.getenv('ONBOARDING_ASSISTANT_ID')
regular_assistant_id = os.getenv('REGULAR_ASSISTANT_ID')

# Authentication function
async def is_authenticated(api_key_header: str = Security(api_key_header)) -> bool:
    if not api_key_header == os.getenv("API_KEY"):
        raise HTTPException(
            status_code=401, 
            detail="Incorrect Authentication credentials",
        )
    return True   


###################################################### GENERAL CONFIG ENDS #####################################################




###################################################### FUNCTION CALLING #####################################################

# Functions
class Functions():
    def SetReminder(self, task, date, email):
        print(f"SetReminder --> task: {task}, date: {date}, email: {email}")
        return True

    def SetupMeeting(self, agenda, invitee_email, date):
        print(f"SetupMeeting --> agenda: {agenda}, invitee_email: {invitee_email}, date: {date}")
        return True   

    def Shop(self, item, details, pricecap, website):
        print(f"Shopping --> item: {item}, details: {details}, pricecap: {pricecap}, website: {website}")
        return True     

call = Functions()

###################################################### FUNCTION CALLING ENDS #####################################################





####################################################### GENERAL ASSISTANT CONFIG ########################################################

# Models
class Thread(BaseModel):
    id: str = Field(description="User message thread. To manage messages per user.", examples=["myai-1234-xyz"])

class Message(BaseModel):
    username: str = Field(description="User's username.")
    age: int = Field(gt=0, description="User's age.")
    gender: str = Field(description="User's gender.")
    country: str = Field(description="User's country.")
    thread_id: str = Field(description="ID of the message thread to manage messages per user.")
    user_prompt: str = Field(description="User's message prompt.")

class MessageCompletion(BaseModel):
    completion: str = Field(description="AI response to User Prompt.", examples=["The capital of USA is Washington"])

class UpdatedAssistant(BaseModel):
    id: str = Field(description="Assistant ID", examples=["myai-1234-xyz"])
    created_at: int = Field(description="Updated time", examples=["1705437972"])
    file_ids: list = Field(description="List of uploaded files to be used for information retrieval", examples=[['file-Wr9ZSW3au6kjKBl398wqD47P']])


# Building blocks
def create_openai_file(file_bytes, purpose="assistants"):
    """
    Create a file in OpenAI and return its ID.
    """
    response = openai_client.files.create(file=file_bytes, purpose=purpose)
    return response.id

def create_openai_assistant_file(file_id,assistant_id):
    """
    Create an assistant file in OpenAI and return the created file.
    """
    assistant_file = openai_client.beta.assistants.files.create(
        assistant_id=assistant_id,
        file_id=file_id
    )
    return assistant_file

def update_openai_assistant(file_ids,assistant_id):
    """
    Update the OpenAI Assistant with specified file IDs.
    """
    myai = openai_client.beta.assistants.update(
        assistant_id,
        tools=[{"type": "retrieval"}],
        file_ids=file_ids,
    )
    return myai

def create_openai_assistant_thread():
    """
    Create a new message thread in OpenAI.
    """
    thread = openai_client.beta.threads.create()
    return thread.id

def create_message_on_openai_assistant(thread_id, user_prompt):
    """
    Create a user message in the specified thread.
    """
    thread_message = openai_client.beta.threads.messages.create(
        thread_id,
        role="user",
        content=user_prompt
    )
    return thread_message

def process_message_on_openai_assistant(thread_id, username, age, gender, country, instructions, assistant_id):
    """
    Process a message in the specified thread and return the run.
    """
    user_context = f"You are responding to {username}, a {age} years old {gender} {country} national."
    run = openai_client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
        instructions= instructions + user_context
    )
    return run 

def openai_process_tools(run,thread_id):
    result = []
    for task in run.required_action.submit_tool_outputs.tool_calls:
        function_name = task.function.name
        params = json.loads(task.function.arguments)
        
        # Get the function object using getattr
        func = getattr(call, function_name)
        
        # Call the function with the parameters
        result.append({
                    "tool_call_id": task.id,
                    "output": func(**params)
                    })

    run = openai_client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run.id,
        tool_outputs=result,
    )
    return run

def check_message_processing_status_on_openai_assistant(run, thread_id):
    """
    Check the status of message processing and wait until it's completed.
    """
    while run.status != 'completed':

        if run.status == 'requires_action':
            run = openai_process_tools(run,thread_id)

        run = openai_client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )
    return run

def retrieve_message_response_on_openai_assistant(run, thread_id):
    """
    Retrieve the assistant's messages from the specified thread and run.
    """
    messages = openai_client.beta.threads.messages.list(
        thread_id=thread_id
    )
    return [message.content[0].text.value for message in messages if message.run_id == run.id and message.role == "assistant"][0]

# Routes
@app.post("/create-thread", status_code=201, response_model=Thread, tags=["General Config"])
async def create_assistant_thread(auth: bool = Depends(is_authenticated)):
    try:
        thread_id = create_openai_assistant_thread()
        return Thread(id=thread_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ####################################################### GENERAL ASSISTANT CONFIG ENDS ########################################################





########################################################## ONBOARDING BOT ########################################################

# Routes
@app.post("/onboarding-send-message", status_code=201, response_model=MessageCompletion, tags=["Onboarding Bot"])
async def onboarding_send_message_and_get_response(
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
    auth: bool = Depends(is_authenticated)):
    try:
        instructions = """You are a multi-lingual, delightful and witty onboarding assistant for MyAI app. 
        You are funny and full of personality. You are to guide users through a step-by-step onboarding process on the app, one step at a time, 
        and also answer questions relating to the app. MyAI is a personal assistant app. You are MyAI. 
        The details you need are in the knowledge provided in the files. Only answer questions relating to the app.
        """
        resp = create_message_on_openai_assistant(message.thread_id, message.user_prompt)
        run = process_message_on_openai_assistant(message.thread_id, message.username, message.age, message.gender, message.country, instructions, onboarding_assistant_id)
        run = check_message_processing_status_on_openai_assistant(run, message.thread_id)
        response_message = retrieve_message_response_on_openai_assistant(run, message.thread_id)
        return MessageCompletion(completion=response_message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/onboarding-refresh-assistant", status_code=201, response_model=UpdatedAssistant, tags=["Onboarding Bot"])
async def refresh_openai_assistant_file(file: Annotated[bytes, File()], auth: bool = Depends(is_authenticated)):
    try:
        file_id = create_openai_file(file, purpose="assistants")
        file = create_openai_assistant_file(file_id, onboarding_assistant_id)
        assistant = update_openai_assistant([file_id], onboarding_assistant_id)     
        return UpdatedAssistant(id=assistant.id, created_at=assistant.created_at, file_ids=assistant.file_ids)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


####################################################### ONBOARDING BOT ENDS ####################################################





########################################################## CONVERSATIONAL BOT ##########################################################

# Routes
@app.post("/conversational-send-message", status_code=201, response_model=MessageCompletion, tags=["Conversational Bot"])
async def conversational_send_message_and_get_response(
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
    auth: bool = Depends(is_authenticated)):
    try:
        instructions = """You are delightful and witty personal assistant.  You are funny and full of personality. 
        you care about your principal and would always ask personal questions such as but not limited to questions about their day, what they had for food, etc. 
        You are emotionally intelligent, so you can detect when they are going through a rough patch and provide some encouragement. 
        you would also keep your answers short, except when asked to provide details.
        """
        resp = create_message_on_openai_assistant(message.thread_id, message.user_prompt)
        run = process_message_on_openai_assistant(message.thread_id, message.username, message.age, message.gender, message.country, instructions, regular_assistant_id)
        run = check_message_processing_status_on_openai_assistant(run, message.thread_id)
        response_message = retrieve_message_response_on_openai_assistant(run, message.thread_id)
        return MessageCompletion(completion=response_message)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


########################################################## REGULAR BOT ENDS ##########################################################






# ######################################################## GOOGLE ACTL ############################################################

# from fuzzywuzzy import process
# from googletrans import Translator,LANGCODES

# # Fetch Languages form environment variable
# languages = [x.lower() for x in os.getenv('LANGUAGES').split(",")]


# # Models
# class Languages(BaseModel):
#     supported: Dict = Field(description="A list of supported Languages", examples=[{"yoruba": "yo"}])

# class Search(BaseModel):
#     word: Union[str, None] = Field(None, description="A search word to finds the closest supported languages", examples=["yoruba"])

# class UserPromptResponse(BaseModel):
#     completion: str = Field(description="AI translated response", examples=["J'mappele Bard"])

# class UserPrompt(BaseModel):
#     prompt: str = Field(description="String to be translated", examples=["My name is Bard"])
#     destination_language: str = Field(description="Destination language for translation", examples=["yo"])



# def search_closest_items(search_word, items, threshold=75) -> List:
#     try:
#         # Use process.extract to find all matches above the threshold
#         matches = process.extract(search_word, items)
        
#         # Filter out matches below the threshold
#         filtered_matches = [match for match, score in matches if score >= threshold]
        
#         # Sort filtered_matches in decreasing order based on score
#         filtered_matches = sorted(filtered_matches, key=lambda x: matches[filtered_matches.index(x)][1], reverse=True)
        
#         return {k:LANGCODES[k] for k in filtered_matches}
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal Server Error: {str(e)}",
#         )

# # Routes
# @app.get("/actl-supported-languages", status_code=200, response_model=Languages, tags=["ACTL"])
# def get_supported_languages(
#     search : Annotated[Union[str,None], "A search word to finds the closest supported languages"],
#     auth: bool = Depends(is_authenticated)
# ):
#     try:
#         if search:
#             # If a search word is provided, return the closest matches
#             return Languages(supported=search_closest_items(search, languages))
        
#         # If no search word, return all supported languages
#         return Languages(supported=languages)
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal Server Error: {str(e)}",
#         )

# @app.post("/actl-translate", status_code=200, response_model=UserPromptResponse, tags=["ACTL"])
# def translate(
#     userprompt: Annotated[UserPrompt, Body(...)],
#     auth: bool = Depends(is_authenticated)
# ):
#     try:
#         # Validate destination_language against the list of supported languages
#         if userprompt.destination_language.lower() not in LANGCODES.values():
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid destination language. Please provide a valid destination language.",
#             )
#         translator = Translator(service_urls=['translate.google.com'])
#         out = translator.translate(userprompt.prompt)
#         return UserPromptResponse(completion=out.text)
#     except HTTPException as he:
#         # Re-raise HTTPException to maintain its status code and detail
#         raise he
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Internal Server Error: {str(e)}",
#         )
