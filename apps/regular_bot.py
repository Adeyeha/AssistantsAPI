# Import necessary libraries
import openai
import streamlit as st
import time
import os
from dotenv import load_dotenv
load_dotenv()


# Set your OpenAI Assistant ID here
assistant_id = os.getenv('ASSISTANT_ID')

# Initialize the OpenAI client (ensure to set your API key in the sidebar within the app)
client = openai.Client(api_key=os.getenv('OPENAI_KEY'))

# Get or Create Thread
def get_thread():
    if "thread_id" not in st.session_state:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

def process_message(user_prompt,system_prompt):
    # Add message to thread
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_prompt
    )

    # Create a run with additional instructions
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
        instructions=system_prompt
    )
    return run

def get_generated_response(run):
    # Poll for the run to complete and retrieve the assistant's messages
    while run.status != 'completed':
        time.sleep(1)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )

    # Retrieve messages added by the assistant
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    return [message.content[0].text.value for message in messages if message.run_id == run.id and message.role == "assistant"][0]
    
# Set up the Streamlit page with a title and icon
st.set_page_config(
    page_title="MyAI Multi-Lingual Assistant",
    page_icon="🤖",
    layout="wide"
)
st.title("MyAI Multi-Lingual Assistant")

# Create a sidebar for user context and additional features
st.sidebar.header("User Context")
username = st.sidebar.text_input("User Name", key="username", value="Buddy")

# LLM Prompt
system_prompt = f"""
You are a delightful and witty personal assistant of {username}  You are funny and full of personality. 
You care about your principal and would always ask personal questions such as but not limited to questions about their day, what they had for food, etc. 
You are emotionally intelligent, so you can detect when they are going through a rough patch and provide some encouragement. 
You would also keep your answers short, except when asked to provide details.
"""

# check for messages in session and create if not exists
if "messages" not in st.session_state.keys():
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey buddy, You can ask and tell me anything!"}
    ]

# Display all messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_prompt = st.chat_input()

if user_prompt is not None:
    get_thread()
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.write(user_prompt)


if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Loading..."):
            run = process_message(user_prompt,system_prompt)
            gen_response = get_generated_response(run)
            st.write(gen_response)
    new_ai_message = {"role": "assistant", "content": gen_response}
    st.session_state.messages.append(new_ai_message)

