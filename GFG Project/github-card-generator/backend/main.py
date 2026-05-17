import os
import traceback
import asyncio
import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager

from google.adk import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.genai.types import Content, Part
from agent import github_card_agent, mcp_toolset, CARDS_DIR, STATIC_DIR

# Runner Configuration
runner = Runner(
    app_name="GitHubDevCard",
    agent=github_card_agent,
    session_service=InMemorySessionService(),
    memory_service=InMemoryMemoryService(),
    auto_create_session=True
)

from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n--- FAST SYSTEM READY ---")
    yield
    await mcp_toolset.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

class GenReq(BaseModel):
    username: str
    model: str = "gemini-3.1-flash-lite"


@app.post("/generate")
async def generate(req: GenReq):
    try:
        name = req.username.lstrip('@')
        target_model = req.model
        sys.stderr.write(f"\n--- FAST MISSION: {name} (Model: {target_model}) ---\n")
        sys.stderr.flush()
        
        # Unique session for every request
        session_id = f"s_{name}_{int(datetime.now().timestamp())}"
        try:
            # We pass the requested model as part of the prompt so the agent knows which one to pass to tools
            events = runner.run(
                user_id="u", 
                session_id=session_id, 
                new_message=Content(parts=[Part(text=f"Username: {name}, Model: {target_model}")], role="user")
            )
        except Exception as runner_err:
            if "429" in str(runner_err):
                return {"status": "error", "message": "The AI is currently overwhelmed. Please wait about 30 seconds and try again."}
            raise runner_err
        
        last_tool_output = None
        agent_text = []
        for e in events:
            if e.content and e.content.parts:
                for part in e.content.parts:
                    if part.text: 
                        sys.stderr.write(f"AGENT: {part.text}\n")
                        agent_text.append(part.text)
                    if part.function_call: 
                        sys.stderr.write(f">> {part.function_call.name}({part.function_call.args})\n")
                    if part.function_response and part.function_response.name == "generate_and_save_card":
                        last_tool_output = part.function_response.response
                    sys.stderr.flush()

            if e.error_message:
                sys.stderr.write(f"AGENT ERROR: {e.error_message}\n")
                sys.stderr.flush()
                if "429" in str(e.error_message): 
                    return {"status": "error", "message": "AI Quota Exceeded. Retrying in 30s usually works!"}
                # If we have a fallback card already generated or if it's a tool error that we handled
                continue 

        if last_tool_output:
            return {"status": "success", "message": " ".join(agent_text), **last_tool_output}
        
        # PROACTIVE FALLBACK: If agent didn't call the tool (likely due to quota/error), 
        # we try to run the tools manually to save the day.
        try:
            from mcp_server import scrape_github, analyze_profile, generate_and_save_card
            sys.stderr.write(f"RECOVERY MODE for {name}...\n")
            
            # 1. Scrape
            data = await scrape_github(name)
            if "error" in data:
                return {"status": "error", "message": f"Could not find GitHub user: {name}"}
            
            # 2. Analyze (Analyze profile has its own internal fallback for Gemini errors)
            analysis = await analyze_profile(data)
            
            # 3. Create
            result = await generate_and_save_card(name, data, analysis)
            return {"status": "success", "message": "Mission successful (Recovery Mode)", **result}
            
        except Exception as recovery_err:
            sys.stderr.write(f"RECOVERY FAILED: {recovery_err}\n")
            return {"status": "error", "message": f"Critical Failure: {str(recovery_err)}"}

    except Exception as e:
        sys.stderr.write(f"FAILED: {e}\n")
        sys.stderr.flush()
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
