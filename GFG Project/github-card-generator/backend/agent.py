import os
import sys
from dotenv import load_dotenv
from google.adk import Agent, Runner
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp.client.stdio import StdioServerParameters

load_dotenv()

# Protocol-Safe Pathing
backend_dir = os.path.dirname(os.path.abspath(__file__))
mcp_path = os.path.join(backend_dir, "mcp_server.py")
STATIC_DIR = os.path.join(backend_dir, "static")
CARDS_DIR = os.path.join(STATIC_DIR, "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

mcp_params = StdioConnectionParams(
    server_params=StdioServerParameters(command=sys.executable, args=[mcp_path], env=os.environ.copy()),
    timeout=60.0
)
mcp_toolset = McpToolset(connection_params=mcp_params)

# Clean Agent Brain - Using Gemini 3.1 Flash-Lite
github_card_agent = Agent(
    name="GitHubBot",
    model="gemini-3.1-flash-lite",
    instruction="""You are an expert Python developer building a GitHub Dev Card Generator. The stack is: Google ADK for agent orchestration, MCP (FastMCP) for tools, Gemini 2.5 Flash as the LLM, FastAPI as the backend, and React/HTML as the frontend. Everything deploys to Google Cloud Run. Write clean, modular Python. Prefer uv for dependency management.
    
    SEQUENCE:
    1. SCRAPE: Call 'scrape_github' with the target username.
    2. ANALYZE: Call 'analyze_profile' with the results from scrape_github and the specific 'Model' mentioned in the user message.
    3. CREATE: Call 'generate_and_save_card' with the username, data from step 1, and analysis from step 2.
    
    STRICT RULES:
    - ALWAYS pass the user's requested 'Model' to the 'analyze_profile' tool.
    - ALWAYS call 'generate_and_save_card' at the end.
    - YOUR RESPONSE MUST include a short, high-energy status message about the user's role and vibe (e.g., "The Backend Titan has entered the arena!" or "A Frontend Wizard casting CSS spells").
    - Make the messages feel unique and tailored to the detected role.
    - After saving, confirm completion with your personalized status message.""" ,
    tools=[mcp_toolset]
)
