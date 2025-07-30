import os #for accessing environment variables and checking file paths 
import asyncio #built in module for running asynchronous code
import aiohttp #allows async HTTP requestions 
import json #read and write .json files for caching
from dotenv import load_dotenv #loads .env file so API key is not in code
from rich.console import Console #this and below - make terminal output pretty
from rich.table import Table

# Load .env
load_dotenv() #reads the .env file
API_KEY = os.getenv("API_KEY") #fetches the API key

if not API_KEY: #if key is not loaded properly program will stop
    raise ValueError("API_KEY not found in environment variables")

CACHE_FILE = "weather_cache.json" #local JSON file to store results
console = Console() #using rich to output it nicely 

#async function that sends a request to the weather API 
async def fetch_weather(session, city):
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
      "key": API_KEY,
      "q": city,
    }
    async with session.get(url, params=params) as response: #sends a GET request
        if response.status == 200:
            return await response.json() #analyze the JSON response 
        else:
            console.print(f"[red]Error fetching data for {city}: {response.status}[/red]")
            return None

#checks if cache file exists 
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

#writes the updated cache back to the json file
def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

async def main(cities):
    cache = load_cache() #loads any cached weather data
    results = {} #creates an empty dictionary to store results 
    #start async tasks
    async with aiohttp.ClientSession() as session:
        tasks = []
        for city in cities:
            # Use cache if available
            if city in cache:
                results[city] = cache[city]
                break
            else:
                tasks.append(fetch_weather(session, city))
                uncached_cities.append(city)
                break
        # Run async tasks concurrently
        responses = await asyncio.gather(*tasks) #runs all the fetches at same time
        # Map responses to cities (tasks order == cities without cache)
        uncached_cities = [c for c in cities if c not in cache] #keeps track of cities we need to fetch
        for city, data in zip(uncached_cities, responses): #saves both types to the cache
            if data:
                results[city] = data
                cache[city] = data
        save_cache(cache)


    # Pretty print results using rich 
    table = Table(title="Weather")
    table.add_column("City", style="blue")
    table.add_column("Day", style="cyan")

    # Color based on temp
    for city, data in results.items():
        tempInt = (data["current"]["temp_f"])
    if(tempInt >= 90):
        table.add_column("Temperature (F°)", style="red")
    elif(tempInt >= 70):
        table.add_column("Temperature (F°)", style="yellow")
    elif(tempInt >= 50):
        table.add_column("Temperature (F°)", style="green")
    else:
        table.add_column("Temperature (F°)", style="blue")

    table.add_column("Weather Conditions", style="green")
    table.add_column("Humidity", style="green")
    table.add_column("UV Index", style="green")

    #extracts data from the JSON
    for city, data in results.items():
        day = str(data["current"]["is_day"])
        temp = str(data["current"]["temp_f"])
        weather = data["current"]["condition"]["text"]
        humidity = str(data["current"]["humidity"])
        uv = str(data["current"]["uv"])
        table.add_row(city, day, temp, weather, humidity, uv)

    console.print(table)


#running the program 
#checks if script is being run directly
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2: #makes sure at least one city is passed as command line argument 
        console.print("[red]Please provide city names as arguments[/red]")
        console.print("Example: python weather.py London Paris Tokyo")
        sys.exit(1)
    #calls the main function with the list of cities using asyncio.run
    cities = sys.argv[1:]
    asyncio.run(main(cities))
