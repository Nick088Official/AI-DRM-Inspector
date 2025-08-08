# AI-DRM-Inspector

This project determines if any games in a Steam library have DRM and identifies the type. It achieves this by performing AI-powered web research for each game, a feature not provided by the standard Steam API.

## How does it work?
1. Lets the user select which AI Model to use, and to enter either the SteamID64 or CustomURL of their Profile.
2. It checks on the Steam Input, if none were done it errors out, if the user used their CustomURL, it gets converted to the SteamID64 via the SteamAPI.
4. Loads the 30 days caches, if any.
5. Via Steam API it checks all the games owned in the Profile.
6. Compares the games to the games in the 30 days cache:
  - If it's found, it uses that
  - If it's a miss or expired, it does a web search with a custom google engine that searches on https://reddit.com & https://www.pcgamingwiki.com/, then processed by the AI.
7. Outputs the results, with a table on the website of the games with their DRM status.


## Features
- **Multiple AI Model Support:** Choose between cloud-based models (Google Gemini, Groq) or a locally-run Ollama model for privacy and offline use.
- **Flexible Steam Input:** Works with both SteamID64 and custom vanity URLs.
- **Intelligent Caching:** Caches results for 30 days to reduce API calls and provide near-instant results for previously checked libraries.
- **Focused Web Research:** Uses a Google Programmable Search Engine to query trusted sources like PCGamingWiki, Reddit, and Steam itself.
- **Clean, Organized Output:** Displays results in a simple, easy-to-read table.


## Requirements
- Git
- Python 3.8+
- Pip


## Setup

### 1. Clone the Repository
First, clone the repository to your local machine using Git.

```bash
git clone https://github.com/your-username/AI-DRM-Inspector.git
cd AI-DRM-Inspector
```

### 2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage project dependencies and avoid conflicts.

-   **On Windows:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

-   **On macOS/Linux:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

### 3. Install Dependencies
Install all the required Python packages using pip and the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Install Ollama (Optional)
If you wish to use a locally-run AI model, you must install Ollama. This allows you to run powerful models on your own machine.

1.  Download and install Ollama from the official website: **[https://ollama.com/](https://ollama.com/)**
2.  Once installed, the application will automatically pull the required model (`gemma2:9b-instruct-q4_0`) the first time you select "Ollama" and run a check.

### 5. Configure Environment Variables
This project requires several API keys to function. Create a new file named `.env` in the root of the project directory and populate it with your keys as shown below.

**Note:** If you only plan to use Ollama, you do not need to provide keys for Gemini or Groq.

```
# .env file
STEAM_API_KEY="YOUR_STEAM_API_KEY"
GROQ_API_KEY="YOUR_GROQ_API_KEY"
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GOOGLE_SEARCH_API_KEY="YOUR_GOOGLE_CLOUD_API_KEY"
SEARCH_ENGINE_ID="YOUR_PROGRAMMABLE_SEARCH_ENGINE_ID"
```

**Where to get the required keys:**

*   **`STEAM_API_KEY`**: Obtain your Steam Web API key from the [Steam Community Developers page](https://steamcommunity.com/dev/apikey).
*   **`GEMINI_API_KEY`**: Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
*   **`GROQ_API_KEY`**: Create an account and get your key from the [GroqCloud Console](https://console.groq.com/keys).
*   **`GOOGLE_SEARCH_API_KEY`** & **`SEARCH_ENGINE_ID`**:
    1.  Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
    3.  Go to the [Programmable Search Engine control panel](https://programmablesearchengine.google.com/controlpanel/all) to create a new search engine.
    4.  Get your API key via "Programmatic Access". This will be your `GOOGLE_SEARCH_API_KEY`.
    5.  Under "Sites to search", add the following URLs to ensure focused and relevant results:
        *   `store.steampowered.com/app/*`
        *   `store.steampowered.com/curator/44556220-DRM-Checker/*`
        *   `store.steampowered.com/curator/38523697-DRM-FREE-GAMES/*`
        *   `www.pcgamingwiki.com/*`
        *   `www.reddit.com/*`
    6.  After creation, find the "Search engine ID" on the "Basics" tab of the control panel. This is your `SEARCH_ENGINE_ID`.

### 6. Run the Application
Once the setup and configuration are complete, you can run the Flask web application.

```bash
flask run
```

By default, the application will be accessible at `http://127.0.0.1:5000` in your web browser.


## Usage
1.  After running `flask run`, open your web browser and navigate to `http://127.0.0.1:5000`.
2.  Select the AI model you wish to use from the dropdown menu.
3.  Enter your SteamID64 or your profile's custom URL into the input field. (e.g., `76561197960287930` or `gabelogannewell`).
4.  Click the "Check DRM" button.
5.  Please be patient, the initial check for a large library may take several minutes as it queries for each game. Subsequent checks will be much faster thanks to the cache.
6.  The results will appear in a table below the form.
