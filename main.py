import json
import braintrust
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

logger = braintrust.init_logger(project="PlaylistGenerator")
client = braintrust.wrap_openai(OpenAI())

class Song(BaseModel):
    title: str
    artist: str

class Playlist(BaseModel):
    playlist_name: str
    songs: list[Song]
    total_tracks: int
    total_duration_min: float

class ToolCall(BaseModel):
    tool: str
    arguments: dict
    result: dict | list

class AgentResult(BaseModel):
    """Structured output from the playlist agent."""
    playlist: Playlist | None = None
    response: str = ""
    tool_calls: list[ToolCall] = []

# Mock music catalog
MUSIC_CATALOG = [
    # Energetic
    {"id": "1", "title": "Blinding Lights", "artist": "The Weeknd", "genre": "synth-pop", "mood": "energetic", "duration_sec": 200},
    {"id": "2", "title": "Uptown Funk", "artist": "Bruno Mars", "genre": "pop", "mood": "energetic", "duration_sec": 270},
    {"id": "3", "title": "Can't Stop the Feeling", "artist": "Justin Timberlake", "genre": "pop", "mood": "energetic", "duration_sec": 236},
    {"id": "4", "title": "Don't Stop Me Now", "artist": "Queen", "genre": "rock", "mood": "energetic", "duration_sec": 209},
    {"id": "5", "title": "Titanium", "artist": "David Guetta ft. Sia", "genre": "electronic", "mood": "energetic", "duration_sec": 245},
    {"id": "6", "title": "Levels", "artist": "Avicii", "genre": "electronic", "mood": "energetic", "duration_sec": 180},
    {"id": "7", "title": "Thunder", "artist": "Imagine Dragons", "genre": "rock", "mood": "energetic", "duration_sec": 187},
    {"id": "8", "title": "Stronger", "artist": "Kanye West", "genre": "hip-hop", "mood": "energetic", "duration_sec": 312},
    {"id": "9", "title": "Scary Monsters", "artist": "Skrillex", "genre": "electronic", "mood": "energetic", "duration_sec": 274},
    {"id": "10", "title": "Run the World", "artist": "Beyoncé", "genre": "pop", "mood": "energetic", "duration_sec": 236},
    # Calm
    {"id": "11", "title": "Weightless", "artist": "Marconi Union", "genre": "ambient", "mood": "calm", "duration_sec": 480},
    {"id": "12", "title": "Clair de Lune", "artist": "Debussy", "genre": "classical", "mood": "calm", "duration_sec": 348},
    {"id": "13", "title": "Breathe", "artist": "Télépopmusik", "genre": "electronic", "mood": "calm", "duration_sec": 265},
    {"id": "14", "title": "Gymnopédie No. 1", "artist": "Erik Satie", "genre": "classical", "mood": "calm", "duration_sec": 210},
    {"id": "15", "title": "Holocene", "artist": "Bon Iver", "genre": "indie", "mood": "calm", "duration_sec": 337},
    {"id": "16", "title": "The Night We Met", "artist": "Lord Huron", "genre": "indie", "mood": "calm", "duration_sec": 207},
    {"id": "17", "title": "River Flows in You", "artist": "Yiruma", "genre": "classical", "mood": "calm", "duration_sec": 186},
    {"id": "18", "title": "Skinny Love", "artist": "Bon Iver", "genre": "indie", "mood": "calm", "duration_sec": 232},
    {"id": "19", "title": "Saturn", "artist": "Sleeping at Last", "genre": "indie", "mood": "calm", "duration_sec": 270},
    {"id": "20", "title": "Bloom", "artist": "The Paper Kites", "genre": "indie", "mood": "calm", "duration_sec": 234},
    # Happy
    {"id": "21", "title": "Happy", "artist": "Pharrell Williams", "genre": "pop", "mood": "happy", "duration_sec": 233},
    {"id": "22", "title": "Here Comes the Sun", "artist": "The Beatles", "genre": "rock", "mood": "happy", "duration_sec": 185},
    {"id": "23", "title": "Walking on Sunshine", "artist": "Katrina and the Waves", "genre": "pop", "mood": "happy", "duration_sec": 239},
    {"id": "24", "title": "Good Vibrations", "artist": "The Beach Boys", "genre": "rock", "mood": "happy", "duration_sec": 219},
    {"id": "25", "title": "Three Little Birds", "artist": "Bob Marley", "genre": "reggae", "mood": "happy", "duration_sec": 180},
    {"id": "26", "title": "I Gotta Feeling", "artist": "Black Eyed Peas", "genre": "pop", "mood": "happy", "duration_sec": 289},
    {"id": "27", "title": "Best Day of My Life", "artist": "American Authors", "genre": "rock", "mood": "happy", "duration_sec": 194},
    {"id": "28", "title": "Lovely Day", "artist": "Bill Withers", "genre": "soul", "mood": "happy", "duration_sec": 254},
    {"id": "29", "title": "Mr. Blue Sky", "artist": "Electric Light Orchestra", "genre": "rock", "mood": "happy", "duration_sec": 305},
    {"id": "30", "title": "Dancing Queen", "artist": "ABBA", "genre": "pop", "mood": "happy", "duration_sec": 232},
    # Motivational
    {"id": "31", "title": "Lose Yourself", "artist": "Eminem", "genre": "hip-hop", "mood": "motivational", "duration_sec": 326},
    {"id": "32", "title": "Eye of the Tiger", "artist": "Survivor", "genre": "rock", "mood": "motivational", "duration_sec": 245},
    {"id": "33", "title": "Stronger", "artist": "Kelly Clarkson", "genre": "pop", "mood": "motivational", "duration_sec": 222},
    {"id": "34", "title": "Fight Song", "artist": "Rachel Platten", "genre": "pop", "mood": "motivational", "duration_sec": 204},
    {"id": "35", "title": "Hall of Fame", "artist": "The Script", "genre": "pop", "mood": "motivational", "duration_sec": 202},
    {"id": "36", "title": "Remember the Name", "artist": "Fort Minor", "genre": "hip-hop", "mood": "motivational", "duration_sec": 229},
    {"id": "37", "title": "Believer", "artist": "Imagine Dragons", "genre": "rock", "mood": "motivational", "duration_sec": 204},
    {"id": "38", "title": "Till I Collapse", "artist": "Eminem", "genre": "hip-hop", "mood": "motivational", "duration_sec": 297},
    {"id": "39", "title": "We Will Rock You", "artist": "Queen", "genre": "rock", "mood": "motivational", "duration_sec": 122},
    {"id": "40", "title": "Born This Way", "artist": "Lady Gaga", "genre": "pop", "mood": "motivational", "duration_sec": 260},
    # Melancholy
    {"id": "41", "title": "Someone Like You", "artist": "Adele", "genre": "pop", "mood": "melancholy", "duration_sec": 285},
    {"id": "42", "title": "Mad World", "artist": "Gary Jules", "genre": "indie", "mood": "melancholy", "duration_sec": 193},
    {"id": "43", "title": "Hurt", "artist": "Johnny Cash", "genre": "country", "mood": "melancholy", "duration_sec": 217},
    {"id": "44", "title": "Everybody Hurts", "artist": "R.E.M.", "genre": "rock", "mood": "melancholy", "duration_sec": 312},
    {"id": "45", "title": "Fix You", "artist": "Coldplay", "genre": "rock", "mood": "melancholy", "duration_sec": 295},
    {"id": "46", "title": "Nothing Compares 2 U", "artist": "Sinéad O'Connor", "genre": "pop", "mood": "melancholy", "duration_sec": 310},
    {"id": "47", "title": "Tears in Heaven", "artist": "Eric Clapton", "genre": "rock", "mood": "melancholy", "duration_sec": 274},
    {"id": "48", "title": "The Sound of Silence", "artist": "Simon & Garfunkel", "genre": "folk", "mood": "melancholy", "duration_sec": 187},
    {"id": "49", "title": "Creep", "artist": "Radiohead", "genre": "rock", "mood": "melancholy", "duration_sec": 238},
    {"id": "50", "title": "Black", "artist": "Pearl Jam", "genre": "rock", "mood": "melancholy", "duration_sec": 342},
]

# Tool definitions for OpenAI
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_songs",
            "description": "Search for songs in the catalog by genre or mood",
            "parameters": {
                "type": "object",
                "properties": {
                    "genre": {"type": "string", "description": "Genre to filter by (e.g., rock, pop, electronic, classical, hip-hop, ambient, synth-pop, indie, reggae, soul, country, folk)"},
                    "mood": {"type": "string", "description": "Mood to filter by (e.g., energetic, calm, happy, motivational, melancholy)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_song_details",
            "description": "Get detailed information about a specific song by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "song_id": {"type": "string", "description": "The ID of the song to look up"},
                },
                "required": ["song_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_playlist",
            "description": "Create a playlist with the specified songs",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name of the playlist"},
                    "song_ids": {"type": "array", "items": {"type": "string"}, "description": "List of song IDs to include"},
                },
                "required": ["name", "song_ids"],
            },
        },
    },
]


@braintrust.traced(type="tool")
def search_songs(genre: str = None, mood: str = None) -> list[dict]:
    """Search the catalog by genre and/or mood."""
    results = MUSIC_CATALOG
    if genre:
        results = [s for s in results if s["genre"].lower() == genre.lower()]
    if mood:
        results = [s for s in results if s["mood"].lower() == mood.lower()]
    return [{"id": s["id"], "title": s["title"], "artist": s["artist"]} for s in results]


@braintrust.traced(type="tool")
def get_song_details(song_id: str) -> dict | None:
    """Get full details for a song by ID."""
    for song in MUSIC_CATALOG:
        if song["id"] == song_id:
            return song
    return None


@braintrust.traced(type="tool")
def create_playlist(name: str, song_ids: list[str]) -> dict:
    """Create a playlist with the given songs."""
    songs = []
    total_duration = 0
    for sid in song_ids:
        song = get_song_details(sid)
        if song:
            songs.append({"title": song["title"], "artist": song["artist"]})
            total_duration += song["duration_sec"]

    return {
        "playlist_name": name,
        "songs": songs,
        "total_tracks": len(songs),
        "total_duration_min": round(total_duration / 60, 1),
    }


def handle_tool_call(tool_name: str, arguments: dict) -> str:
    """Execute a tool and return the result as a string."""
    if tool_name == "search_songs":
        result = search_songs(arguments.get("genre"), arguments.get("mood"))
    elif tool_name == "get_song_details":
        result = get_song_details(arguments["song_id"])
    elif tool_name == "create_playlist":
        result = create_playlist(arguments["name"], arguments["song_ids"])
    else:
        result = {"error": f"Unknown tool: {tool_name}"}

    return json.dumps(result)


DEFAULT_SYSTEM_PROMPT = "You are a helpful music assistant that creates playlists. Use the available tools to search for songs and create playlists based on user requests. Always search for songs first, then create a playlist with your selections."
DEFAULT_MODEL = "gpt-4o-mini"

@braintrust.traced
def run_agent(user_request: str, model: str = None, system_prompt: str = None) -> AgentResult:
    """Run the playlist agent with the given user request."""
    model = model or DEFAULT_MODEL
    system_prompt = system_prompt or DEFAULT_SYSTEM_PROMPT

    print(f"\n{'='*50}")
    print(f"User Request: {user_request}")
    print('='*50)

    result = AgentResult()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_request},
    ]

    while True:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
        )

        message = response.choices[0].message

        # If no tool calls, we're done
        if not message.tool_calls:
            print(f"\nAssistant: {message.content}")
            result.response = message.content
            return result.model_dump()

        # Process tool calls
        messages.append(message)

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"\n→ Calling tool: {tool_name}")
            print(f"  Arguments: {arguments}")

            tool_result = handle_tool_call(tool_name, arguments)
            tool_result_parsed = json.loads(tool_result)

            print(f"  Result: {tool_result}")

            # Track tool calls for observability
            result.tool_calls.append(ToolCall(
                tool=tool_name,
                arguments=arguments,
                result=tool_result_parsed,
            ))

            # Capture the playlist if one was created
            if tool_name == "create_playlist":
                result.playlist = Playlist(**tool_result_parsed)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

#TODO You'll likely want to create some logs. Use uv run main.py after you have instrumented the code with tracing to interact with your agent.
def main():
    print("Playlist Generator Agent")
    print("Type 'quit' to exit\n")

    while True:
        user_input = input("What kind of playlist would you like? > ").strip()
        if user_input.lower() in ("quit", "exit", "q"):
            break
        if user_input:
            result = run_agent(user_input)
            if result["playlist"]:
                print(f"\n--- Playlist Created ---")
                print(f"Name: {result['playlist']['playlist_name']}")
                print(f"Tracks: {result['playlist']['total_tracks']}")
                print(f"Duration: {result['playlist']['total_duration_min']} minutes")


if __name__ == "__main__":
    main()
