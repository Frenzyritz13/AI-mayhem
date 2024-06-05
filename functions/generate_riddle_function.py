import requests  
from openai import OpenAI
import json
import os

  
def get_directions(api_key, start, end):  
    # start and end are place ids
    directions_url = "https://maps.googleapis.com/maps/api/directions/json"  
    params = {
        'origin': f'place_id:{start}',
        'destination': f'place_id:{end}',
        'key': api_key
    }
      
    response = requests.get(directions_url, params=params)  
    directions = response.json()  
    return directions  
  
def get_notable_sights(api_key, path):  
    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"  
    notable_sights = []  
      
    # Extract points from the path  
    points = [step['end_location'] for step in path['legs'][0]['steps']]  
    
    # specify such included types that will make sense to be used to generate a 
    # riddle. for example, the "route" type is not included because it is not
    # a place thatthat make for a good riddle fodder.
    included_types = [
        "amusement_park",
        "aquarium",
        "art_gallery",
        "bakery",
        "bar",
        "book_store",
        "cafe",
        "campground",
        "church",
        "hindu_temple",
        "mosque",
        "city_hall",
        "clothing_store",
        "convenience_store",
        "department_store",
        "electronics_store",
        "florist",
        "furniture_store",
        "grocery_or_supermarket",
        "hardware_store",
        "home_goods_store",
        "jewelry_store",
        "liquor_store",
        "meal_delivery",
        "meal_takeaway",
        "movie_theater",
        "museum",
        "night_club",
        "park",
        "restaurant",
        "shopping_mall",
        "spa",
        "store",
        "zoo",
        "route",
        "political",
        "point_of_interest",
    ]
      
    for point in points:  
        params = {  
            'location': f"{point['lat']},{point['lng']}",  
            'radius': 10,  
            'key': api_key,  
            # 'type': "|".join(included_types)
        }
          
        response = requests.get(places_url, params=params)  
        results = response.json().get('results', [])  
          
        for place in results:  
            notable_sights.append({  
                'name': place.get('name'),  
                'location': place.get('geometry', {}).get('location')  
            })
      
    return notable_sights  
  
def generate_riddle(api_key, start, end):  
    # Get directions and notable sights
    directions = get_directions(api_key, start, end)  
    notable_sights = get_notable_sights(api_key, directions['routes'][0])  
    # Generate a riddle based on the notable sights  
    # get the place details for the start and end points
    places_url = "https://maps.googleapis.com/maps/api/place/details/json"

    # use only the name key in the notable_sights list
    notable_sights = [sight['name'] for sight in notable_sights]

    params = {
        'place_id': start,
        'key': api_key
    }

    response = requests.get(places_url, params=params)
    start_name = response.json().get('result', {}).get('name')

    params = {
        'place_id': end,
        'key': api_key
    }

    response = requests.get(places_url, params=params)
    end_name = response.json().get('result', {}).get('name')

    prompt = (
        "You have a list of some notable points that lie in a path leading to some destination. "
        "Build a riddle that uses some of these points (the ones you think are best suited to be used) as "
        "clues to the destination. The riddle should be such that the answer to the riddle is the destination. "
        "Don't mention the destination name in the riddle. "
        f"The start location is {start_name} and more importantly, the destination is {end_name}. "
        f"The notable points are as follows: {notable_sights}."
        "Only output the riddle and nothing else."
    )
    
    openai_client = OpenAI(api_key="")

    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ]
    )

    riddle = response.choices[0].message.content
    # TODO generate image and voice over to the riddle
    return riddle
