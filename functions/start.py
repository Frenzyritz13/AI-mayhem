from typing import Dict
from openai import OpenAI
import requests
import os
import time
from logging import getLogger

from functions.generate_riddle_function import generate_riddle
# from functions.settings import get_settings

logger = getLogger(__name__)

current_target = 0

def get_places(api_key, location, radius, keywords):
    base_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    places = []

    for keyword in keywords:
        params = {
            "location": location,
            "radius": radius,
            "keyword": keyword,
            "key": api_key,
        }

        response = requests.get(base_url, params=params)

        results = response.json().get("results", [])

        for place in results[:2]:  # Get top 2 places for each keyword
            places.append({  
                'name': place.get('name'),
                'place_id': place.get('place_id'),
                'lat_long': str(place.get("geometry").get('location').get('lat')) + ',' + str(place.get("geometry").get('location').get('lng'))
            })

    # return five random places
    places = places[:5]

    # define a global list_places object of type Dict[str, str]
    global list_places

    # generate an ordered list from places
    list_places = {index: place for index, place in enumerate(places)}

    print("All places", list_places)

def get_keywords(interests: str):
    """Generates a list of keywords based on the user's interests.

    This function uses OpenAI's GPT-4o for generating this list.

    Args:
        interests (str): The user's interests.
    """
    import json
    prompt = (
        "This list of interests come from a group of people interested in "
        "exploring a city. Take this list of interests and generate exact keywords "
        "to pass to the Google Maps Places API to get the coordinates for them. The "
        "interests are: {}. The keywords should be a list of strings. "
        "Output only the list and nothing else ".format(interests)
    )

    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    keywords = response.choices[0].message.content.split(", ")
    return keywords


def start_game(current_location: str, user_interests: str):
    """Generates a list of all possible waypoints and the first ever riddle.

    Args:
        current_location (str): The user's current location.
    """
    global start_time
    start_time = time.time()
    api_key = os.getenv("MAPS_API_KEY")
    keywords = get_keywords(interests=user_interests)
    get_places(api_key, current_location, 1000, keywords)

    logger.info("Current Location: ", current_location)

    # get the place ID for the current location
    place_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": current_location,
        "radius": 50,
        "key": api_key
    }
    response = requests.get(place_url, params=params)
    current_location = response.json().get("results", [])[0]["place_id"]

    # set the current target to 0
    global current_target
    current_target = 0

    first_riddle = generate_riddle(api_key, current_location, list_places[0]["place_id"])
    return first_riddle

def verify(current_location: str, image: str = None):
    """Verifies the answer to the riddle.

    Args:
        image (str): The image of the destination that is the answer to the riddle.
        current_location (str): The user's current location in coordinates.
    """
    # check if the time has run out
    if time.time() - start_time > 3600:
        return "The time has run out. You have taken too long to complete the game. You have covered {} points.".format(current_target)

    # check if the current location coordinates match the verify input coordinates upto 2 metres
    range_of_error = 2
    # get the coordinates of the current location
    current_location = current_location.split(",")
    # get the coordinates of the destination
    # print("Current target", current_target)
    destination = list_places[current_target]["lat_long"].split(",")

    # check if the coordinates match
    if abs(float(current_location[0]) - float(destination[0])) <= range_of_error and abs(float(current_location[1]) - float(destination[1])) <= range_of_error:
        # increment the current target
        current_target += 1
        # check if the current target is the last target
        if current_target == len(list_places) - 1:
            return "Congratulations! You have reached the destination. You have successfully completed the game."
        else:
            # get the next riddle
            next_riddle = generate_riddle(os.getenv("MAPS_API_KEY"), list_places[current_target - 1]["place_id"], list_places[current_target]["place_id"])
            return next_riddle
    
    
    return "Sorry, the answer is incorrect. Please try again. You can also ask for a hint if you need one."

def get_hint():
    """Returns a hint for the current riddle."""
    # TODO: only allow a fixed number of hints
    # find the current target location
    current_target_location = list_places[current_target]["name"]

    # get the place details for the current target location
    places_url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        'place_id': list_places[current_target]["place_id"],
        'key': os.getenv("MAPS_API_KEY")
    }

    response = requests.get(places_url, params=params)
    place_details = response.json().get('result', {})

    # call the OpenAI API to generate a hint
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = (
        "You are stuck at a location and need a hint to move forward. "
        "The hint should be a sentence that gives a clue about the destination. "
        "The target location which is also the destination is {}. "
        "The details of the location are as follows: {}."
        "Output only the hint and nothing else.".format(current_target_location, place_details)
    )

    response = openai_client.chat.completions.create(
        # TODO: Change the model to GPT-4o
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    hint = response.choices[0].message.content
    return hint
