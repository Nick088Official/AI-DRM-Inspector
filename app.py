from dotenv import load_dotenv
import json
import os
import requests
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google import genai
from google.genai import types
from groq import Groq
import ollama
from ollama import Options


# Load environment variables from .env file
load_dotenv()

# Configuration
STEAM_API_KEY = os.environ.get("STEAM_API_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GOOGLE_SEARCH_API_KEY = os.environ.get("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.environ.get("SEARCH_ENGINE_ID")


ID_STEAM_API_URL = "http://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/"
GAMES_STEAM_API_URL = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/"
CACHE_FILE = 'cache.json'
CACHE_EXPIRATION_DAYS = 30 # How long to keep cache entries valid


app = Flask(__name__)

# --- Initialize API Clients ---
# Gemini
client = genai.Client(api_key=GEMINI_API_KEY)
gemini_model = "gemini-2.5-pro"


# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)


# Groq
groq_client = Groq(api_key=GROQ_API_KEY)
groq_model = "moonshotai/kimi-k2-instruct" 


# Ollama
ollama_model = "gemma3n:e4b"


# AI Settings
temperature=0.5
max_output_tokens=1024



# prompt for web search
BASE_PROMPT = """
What is the DRM for the STEAM PC game '{game_name}'?
- If the game has Denuvo, respond with ONLY the word "Denuvo".
- If it has another known DRM (like Steam DRM), respond with ONLY the name of the DRM.
- If the game is DRM-Free, respond with ONLY the phrase "DRM-Free".
- If you cannot determine the DRM, respond with "Could not be determined".
- Focus only on the STEAM version of the game.
- Be extremely concise. Your entire response should be just the DRM status.
"""

WEB_CONTEXT_BLOCK = """

Base your answer ONLY on the following real-time web search context:
<context>
{search_context}
</context>
"""


# Caching Functions 
def load_cache():
    """Loads the appid-to-DRM cache from a JSON file."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_cache(cache):
    """Saves the cache to a JSON file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=4)



def perform_web_search(query):
    """Performs a Google search and returns the top snippets."""
    try:
        service = build("customsearch", "v1", developerKey=GOOGLE_SEARCH_API_KEY)
        # cse: Custom Search Engine
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID, num=5).execute()
        
        # Extract the snippets from the search results
        snippets = [item['snippet'] for item in res.get('items', [])]
        return " ".join(snippets)
    except Exception as e:
        print(f"Error performing web search for '{query}': {e}")
        return "" # Return empty string on failure


# AI 
def get_drm_from_gemini(prompt):
    try:
        response = client.models.generate_content(
            model=gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                tools=[grounding_tool],
             )
        )
        return response.text.strip().replace('\n', ' ')
    except Exception as e:
        print(f"Error querying Gemini API for {prompt}: {e}")
        return "Error: Could not get data from Gemini"


def get_drm_from_groq(prompt):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=groq_model,
            temperature=temperature,
            max_completion_tokens=max_output_tokens,
        )
        return chat_completion.choices[0].message.content.strip().replace('\n', ' ')
    except Exception as e:
        print(f"Error querying Groq API for {prompt}: {e}")
        return "Error: Could not get data from Groq"


def get_drm_from_ollama(prompt):
    try:
        ollama.pull(ollama_model)
        response = ollama.generate(
            model=ollama_model,
            prompt=prompt,
            options=Options(
                temperature=temperature,
                num_predict=max_output_tokens
            ),
        )
        return response['response'].strip().replace('\n', ' ')
    except Exception as e:
        print(f"Error querying Ollama API for {prompt}: {e}")
        return "Error: Could not get data from Ollama"


# Main Routes
@app.route('/')
def index():
    return render_template('index.html')


# Import the request object from flask at the top of your file
from markupsafe import escape

# Change the route to a fixed path
@app.route('/say')
def test():
    # Get the data from a query parameter named 'prompt'
    # .get() is safe and returns None if the parameter doesn't exist
    aprompt = request.args.get('prompt', '') # The '' is a default value

    # Your existing logic
    b = get_drm_from_gemini(aprompt)
    b = escape(b)  # Escape the response to prevent XSS
    # DANGEROUS: This is vulnerable to XSS, which is what you're testing
    return f"Response is: {escape(b)}" 

@app.route('/check_drm', methods=['POST'])
def check_drm():
    """Handles the API request to check for DRM using AI."""
    steamInput = request.get_json().get('steamInput')
    model_choice = request.get_json().get('ai_model', 'groq')
    if not steamInput:
        return jsonify({"error": "SteamID64 or CustomURL is required."}), 400
    
    # 0. Convert CustomURL to SteamID64 if necessary
    if steamInput.isdigit():
        steam_id = steamInput
    else:
        params = {'key': STEAM_API_KEY, 'vanityurl': steamInput, 'format': 'json', 'include_appinfo': True}
        try:
            response = requests.get(ID_STEAM_API_URL, params=params)
            response.raise_for_status()
            steam_id = response.json().get('response', {}).get('steamid', [])
        except requests.exceptions.RequestException as e:
            return jsonify({"error": f"Could not connect to Steam API: {e}"}), 500

    # 1. Load the cache
    cache = load_cache()
    
    # 2. Get owned games from Steam API
    params = {'key': STEAM_API_KEY, 'steamid': steam_id, 'format': 'json', 'include_appinfo': True}
    try:
        response = requests.get(GAMES_STEAM_API_URL, params=params)
        response.raise_for_status()
        games_data = response.json().get('response', {}).get('games', [])
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Could not connect to Steam API: {e}"}), 500

    results = []
    current_time = datetime.now(timezone.utc).isoformat()

    # --- TESTING MODIFICATION ---
    # Slice the list to get only the first 2 games.
    # To test all games again, simply comment out or delete the next line.
    games_to_process = games_data
    # --------------------------

    for game in games_to_process:
        appid = str(game['appid'])
        game_name = game['name']
        
        # 3. Check cache first
        if appid in cache:
            entry = cache[appid]
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if datetime.now(timezone.utc) - entry_time < timedelta(days=CACHE_EXPIRATION_DAYS):
                print(f"CACHE HIT for {game_name}")
                drm_info = entry['drm']
            else:
                 # Cache expired, research again
                print(f"CACHE EXPIRED for {game_name}. Researching again...")
                drm_info = get_drm_from_gemini(game_name)
                cache[appid] = {'drm': drm_info, 'timestamp': current_time}
        else:
            # 4. If not in cache, call API
            print(f"CACHE MISS for {game_name}. Querying using {model_choice.upper()}...")


            final_prompt = BASE_PROMPT.format(game_name=game_name)

            if model_choice == 'gemini':
                # Gemini uses its internal tool, so it only needs the base prompt
                drm_info = get_drm_from_gemini(final_prompt)
            elif model_choice == 'groq':
                # Groq needs the manual search context appended to the base prompt
                search_context = perform_web_search(f"{game_name} PC DRM Steam")
                final_prompt += WEB_CONTEXT_BLOCK.format(search_context=search_context)
            elif model_choice == 'ollama':
                # Ollama needs the manual search context appended to the base prompt
                search_context = perform_web_search(f"{game_name} PC DRM Steam")
                final_prompt += WEB_CONTEXT_BLOCK.format(search_context=search_context)
                drm_info = get_drm_from_ollama(final_prompt)


            cache[appid] = {'drm': drm_info, 'timestamp': current_time}

        results.append({"name": game_name, "appid": appid, "drm": drm_info})

    # 5. Save the updated cache and return results
    save_cache(cache)
    results.sort(key=lambda x: x['name'])
    return jsonify({"games": results})