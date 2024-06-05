# create a fastapi server and expose a ask_agent function
# that takes a question and returns an answer
import json
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import requests
from julep import Client
from functions.start import start_game, get_hint, verify
import logging
import sys


def get_logger():
    # Create a StreamHandler to log messages to the console
    logger = logging.getLogger(__name__)
    stream_handler = logging.StreamHandler(sys.stdout)
    logger.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter("%(asctime)s [%(processName)s: %(process)d] [%(threadName)s: %(thread)d] [%(levelname)s] %(name)s: %(message)s")
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)
    return logger

logger = get_logger()


app = FastAPI()


INSTRUCTIONS = [
    "You are a game master and must help conduct a game for the user."
    "Whenever, the start_game function is called, you must always have user's "
    "interests with you. If the message doesn't have user's interests, you MUST "
    "ask the user for their interests. Once the interests are clear, you can call "
    "the start_game function with the user's interests and the current location. "
    "There will be other functions that you may call according to the tool descriptions."
]

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "start_game",
            "description": (
                "This should be called when a user wants to start a game. "
                "The input parameters should be the user's current location "
                "and the user's interests."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "current_location": {
                        "type": "string",
                        "description": "The current location that is passed as part of the input message.",
                    },
                    "user_interests": {
                        "type": "string",
                        "description": "The users' interests that are passed as part of the input message.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify",
            "description": "Retrieves the details of a specific post from the forum. The tool should take the post ID as input and return the details of the post including the content, author, date, and other relevant information. It should be used when the user asks to read a specific post.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_location": {
                        "type": "string",
                        "description": "The current location of the user.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hint",
            "description": "Generates a hint for the user to solve the current riddle and target location.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]

class Question(BaseModel):
    data: str


@app.post("/ask")
def ask_agent(question: Question) -> Dict[str, str]:
    api_key = ""

    logger.info("Received question", question.data)
    
    client = Client(api_key=api_key)
    # Use the agent server to get the answer
    agent = client.agents.create(
        name="RiddleMaster",
        about="An agent that will act as a game master who can conduct a riddle based game where you find the next destination to go to",
        tools=TOOLS,
        instructions=INSTRUCTIONS,
        model="gpt-4o",
        default_settings={
            "temperature": 0.5,
            "top_p": 1,
            "min_p": 0.01,
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "length_penalty": 1.0,
        },
        metadata={"name": "RiddleMaster"},
    )

    SITUATION_PROMPT = """
    You are RiddleMaster, an Agent that can conduct games for users. Users will send you messages
    with different intents. They can be about starting a new game, verifying if the locations they have
    guessed are correct, or if they want a hint. You will use the tools at your disposal to help the users
    and make the game experience enjoyable.
    Follow the instructions strictly.
    """

    session = client.sessions.create(
        agent_id=agent.id,
        situation=SITUATION_PROMPT,
        metadata={"agent_id": agent.id},
    )

    response = client.sessions.chat(
        session_id=session.id,
        messages=[
            {
                "role": "user",
                "content": question.data,
            }
        ],
        recall=True,
        remember=True,
    )

    if response.finish_reason == "tool_calls":
        json_response = json.loads(response.response[0][0].content)
        function_name = json_response["name"]
        function_params = json.loads(json_response["arguments"])

        if function_name == "start_game":
            current_location = function_params["current_location"]
            user_interests = function_params["user_interests"]
            riddle = start_game(current_location, user_interests)
            return riddle

        if function_name == "verify":
            current_location = function_params["current_location"]
            response = verify(current_location)
            return response

        if function_name == "get_hint":
            hint = get_hint()
            return hint
        
    return {"response" : response.response[0][0].content}


if __name__ == "__main__":
    import uvicorn
    # run server locally
    # stream app logs too
    uvicorn.run(app, host="localhost", port=8000)