import os
import httpx
import asyncio
import sys
from datetime import datetime
from collections import Counter
from mcp.server.fastmcp import FastMCP
from bs4 import BeautifulSoup
from jinja2 import Template
import json

# Initialize FastMCP
mcp = FastMCP("GitHubDevCard")

# Configuration
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARDS_DIR = os.path.join(BASE_DIR, "static", "cards")
os.makedirs(CARDS_DIR, exist_ok=True)

def log(msg):
    sys.stderr.write(f"LOG: {msg}\n")
    sys.stderr.flush()

def get_gh_headers():
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers

@mcp.tool()
async def scrape_github(username: str) -> dict:
    """FAST SCRAPE: Parallelized GitHub data fetching."""
    clean_name = username.lstrip('@')
    log(f"Speed-Scraping: {clean_name}")
    
    async with httpx.AsyncClient(headers=get_gh_headers(), timeout=15.0) as client:
        # Launch all 3 network tasks simultaneously
        tasks = [
            client.get(f"{GITHUB_API_BASE}/users/{clean_name}"),
            client.get(f"{GITHUB_API_BASE}/users/{clean_name}/repos?sort=stars&per_page=10"),
            client.get(f"https://github.com/users/{clean_name}/contributions")
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check primary responses
        if isinstance(results[0], Exception) or results[0].status_code != 200:
            return {"error": "User not found or GitHub API down."}
            
        profile = results[0].json()
        repos = results[1].json() if not isinstance(results[1], Exception) else []
        
        # Fast Streak Calculation
        streak = 0
        if not isinstance(results[2], Exception) and results[2].status_code == 200:
            soup = BeautifulSoup(results[2].text, "lxml" if "lxml" in sys.modules else "html.parser")
            days = soup.find_all("td", class_="ContributionCalendar-day")
            for day in reversed(days):
                level = day.get("data-level")
                if level and int(level) > 0: streak += 1
                elif streak > 0: break
        
        return {
            "name": profile.get("name") or clean_name,
            "avatar": profile.get("avatar_url"),
            "bio": profile.get("bio", ""),
            "company": profile.get("company", ""),
            "repos": [{"name": r["name"], "stars": r["stargazers_count"]} for r in repos[:5]],
            "followers": profile.get("followers", 0),
            "total_repos": profile.get("public_repos", 0),
            "streak": streak,
            "languages": list(set([r["language"] for r in repos if r["language"]]))[:3]
        }

@mcp.tool()
async def analyze_profile(github_data: dict, model: str = "auto") -> dict:
    """FAST ANALYZE: Role-aware analysis with Smart Model Switching."""
    followers = github_data.get("followers", 0)
    username = github_data.get("login", "the user")
    
    # 1. Smart Model Selection
    selected_model = model
    if model == "auto":
        # Pro for high-impact users, Flash for speed
        selected_model = "gemini-3.1-pro-preview" if (followers > 5000) else "gemini-3.1-flash-lite"
    
    log(f"Smart Analysis: {username} | Followers: {followers} | Model: {selected_model}")
    
    prompt = (
        f"JSON ONLY. Analyze this GitHub profile for '{username}': {json.dumps(github_data)}. "
        "IMPORTANT: Use your internal knowledge for famous developers to provide a respectful and highly specific role, vibe, and roast. "
        "\nCategories: HACKER, BUILDER, RESEARCHER, DESIGNER, ARCHITECT, WIZARD, NINJA, ENGINEER, EDUCATOR. "
        "\nAvailable Themes: hacker, cyberpunk, builder, researcher, designer, wizard, ninja, architect, academic, legend. "
        "Return JSON: {role, vibe, skills[], theme, level, rpg{Focus, Velocity, Impact}, roast}."
    )
    
    async def call_gemini(m):
        async with httpx.AsyncClient() as client:
            return await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={GOOGLE_API_KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json"}},
                timeout=25.0
            )

    res = await call_gemini(selected_model)
    
    # 2. Smart Retry: If selected model fails, try the other one before falling back to heuristics
    if res.status_code == 429:
        alt_model = "gemini-1.5-flash" if selected_model == "gemini-1.5-pro" else "gemini-1.5-pro"
        log(f"Quota hit for {selected_model}, retrying with {alt_model}...")
        res = await call_gemini(alt_model)

    if res.status_code != 200:
        log(f"All Models Busy: {res.status_code}")
        # --- HEURISTIC ANALYSIS ENGINE (Fallback) ---
        log("Running Heuristic Analysis...")
        
        followers = github_data.get("followers", 0)
        repos = github_data.get("total_repos", 0)
        bio = (github_data.get("bio") or "").lower()
        langs = github_data.get("languages", [])
        primary_lang = langs[0] if langs else "Coding"
        streak = github_data.get("streak", 0)
        
        # 1. Determine Role
        role = f"{primary_lang.upper()}-ENGINEER"
        theme = "builder"
        
        # Priority 1: Security/Cyber
        if any(x in bio for x in ["vulnerabilit", "exploit", "ghost", "bug", "malware", "cyber", "pentest", "security"]):
            role = "CYBER-AGENT"; theme = "cyberpunk"
        # Priority 2: Traditional Hacking
        elif "hack" in bio:
            role = "SYSTEM-HACKER"; theme = "hacker"
        # Priority 3: Specialized Roles
        elif any(x in bio for x in ["teach", "tutor", "learn", "educat", "professor", "student"]): 
            role = "TECH-ACADEMIC"; theme = "academic"
        elif any(x in bio for x in ["wizard", "magic", "spell", "sorcerer"]):
            role = "CODE-WIZARD"; theme = "wizard"
        elif any(x in bio for x in ["ninja", "stealth", "swift"]):
            role = "CODE-NINJA"; theme = "ninja"
        # Priority 4: Stats-based
        elif followers > 2000:
            role = "OPEN-SOURCE-LEGEND"; theme = "legend"
        elif any(x in bio for x in ["architect", "design", "structure"]) or repos > 100:
            role = "SYSTEM-ARCHITECT"; theme = "architect"
        elif any(x in bio for x in ["design", "ui", "ux", "art", "creative"]):
            role = "VISUAL-DESIGNER"; theme = "designer"
        elif any(x in bio for x in ["research", "science", "data", "analysis"]):
            role = "DATA-RESEARCHER"; theme = "researcher"
        
        log(f"Heuristic Match -> Role: {role} | Theme: {theme}")
        
        # 2. Dynamic Vibe
        if theme == "academic":
            vibe = f"Sharing knowledge through {repos} educational repositories. The scholar of the digital age."
        elif theme == "researcher":
            vibe = f"Uncovering insights from the void. {repos} repositories of pure discovery."
        elif theme == "wizard":
            vibe = f"Casting complex {primary_lang} spells. Turning bugs into features with arcane logic."
        elif theme == "ninja":
            vibe = f"Executing code with stealth and precision. A master of the {primary_lang} shadows."
        elif theme == "architect":
            vibe = f"Structuring the foundations of the future. {repos} blueprints for excellence."
        elif theme == "cyberpunk":
            vibe = f"Bypassing limits and breaching new frontiers. Data is the new currency."
        elif theme == "legend":
            vibe = f"A legendary figure with {followers:,} followers. Their code is the industry standard."
        elif theme == "designer":
            vibe = f"Where aesthetics meets functionality. Crafting beautiful digital experiences."
        elif streak > 10:
            vibe = f"Consistency is king. Currently on a blazing {streak}-day commit streak."
        else:
            vibe = f"Crafting the future with {primary_lang} and {repos} public projects."

        # 3. Data-Driven Roasts (Pick the best fit)
        if followers > 10000 and repos < 10:
            roast = f"With {followers:,} followers and only {repos} repos, you're more of a celebrity than a coder. Stop tweeting and start committing."
        elif repos > 100 and followers < 50:
            roast = f"100+ repositories and under 50 followers? You're basically shouting into an empty void. Does anyone actually use your code?"
        elif not bio:
            roast = f"An empty bio? How mysterious. Or maybe you're just too lazy to write 160 characters about your {repos} repos."
        elif theme == "cyberpunk":
            roast = "You call yourself a hacker, but the only thing you've ever breached is your own 'Hello World' program."
        elif theme == "academic":
            roast = "You spend so much time teaching 'How to Code' that you've forgotten how to actually build anything original."
        elif theme == "wizard":
            roast = "Your 'magic' is just a bunch of nested try-except blocks, isn't it? Even Gandalf couldn't debug your spaghetti code."
        elif theme == "ninja":
            roast = "A ninja? More like a ghost. Nobody sees your code because nobody actually stars your repos."
        elif primary_lang == "JavaScript":
            roast = "Another JavaScript developer? How original. I bet your 'node_modules' folder is larger than your actual impact on the industry."
        else:
            roast = f"A {primary_lang} enthusiast? That's cute. It's 2026, we've mostly moved on, but it's nice that you're keeping the classics alive."

        # Special case for High-Impact Legends (Generic detection)
        if followers > 10000:
            role = f"LEGENDARY-{role.split('-')[-1]}" if "-" in role else f"LEGENDARY-{role}"
            vibe = f"A prominent figure in the tech space with {followers:,} followers. Their code shapes the industry."
            roast = f"With {followers:,} followers, you're basically a tech deity. I'd roast you, but I'm afraid your fans would debug my life."

        return {
            "role": role,
            "vibe": vibe,
            "skills": langs[:3],
            "theme": theme,
            "level": "LEGEND" if followers > 2000 else "MASTER" if followers > 200 else "LEARNER",
            "rpg": {
                "Focus": min(100, 60 + (streak * 3 if streak < 10 else 40)),
                "Velocity": min(100, 40 + (repos // 2)),
                "Impact": min(100, 30 + (followers // 50))
            },
            "roast": roast
        }

    try:
        data = json.loads(res.json()['candidates'][0]['content']['parts'][0]['text'])
        # Enforce user rule: Hackers use cyberpunk theme
        if "HACKER" in data.get("role", "").upper():
            data["theme"] = "cyberpunk"
        return data
    except (KeyError, IndexError, json.JSONDecodeError):
        log("Failed to parse Gemini response, using fallback.")
        return {
            "role": "LEGENDARY-BUILDER",
            "vibe": f"Building the future using {github_data.get('languages', ['the force'])}.",
            "skills": github_data.get("languages", ["GitHub"]),
            "theme": "builder",
            "level": "LEGEND",
            "rpg": {"Focus": 85, "Velocity": 85, "Impact": 85},
            "roast": "Your code is so elegant it probably writes itself (Fallback Roast)."
        }

def clean_html(text):
    return text.replace('"', '&quot;').replace("'", "&#39;").replace("<", "&lt;").replace(">", "&gt;")

@mcp.tool()
async def generate_and_save_card(username: str, data: dict, analysis: dict) -> dict:
    """FAST CREATE: Atomic render and save."""
    log(f"Rendering: {username}")
    clean_name = username.lstrip('@')
    
    # Defensive key access & escaping (Force string conversion to prevent crashes)
    theme_id = str(analysis.get("theme", "builder")).lower()
    level = str(analysis.get("level", "LEARNER")).upper()
    role_tag = clean_html(str(analysis.get("role", f"{level}-BUILDER")).upper())
    vibe = clean_html(str(analysis.get("vibe", "Just another dev.")))
    roast = clean_html(str(analysis.get("roast", "No roast available.")))
    rpg = analysis.get("rpg", {"Focus": 50, "Velocity": 50, "Impact": 50})
    
    # Ensure skills is a list of strings
    raw_skills = analysis.get("skills", data.get("languages", []))
    if not isinstance(raw_skills, list): raw_skills = [str(raw_skills)]
    skills = [clean_html(str(s)) for s in raw_skills]
    
    themes = {
        "hacker": {"bg": "linear-gradient(180deg, #050505 0%, #0c1a10 100%)", "border": "#22c55e", "text": "#4ade80", "tag": "HACKER", "accent": "#22c55e", "shadow": "rgba(34, 197, 94, 0.3)"},
        "cyberpunk": {"bg": "linear-gradient(180deg, #0a0a0a 0%, #1a0b1a 100%)", "border": "#d946ef", "text": "#22d3ee", "tag": "AGENT", "accent": "#d946ef", "shadow": "rgba(217, 70, 239, 0.3)"},
        "builder": {"bg": "linear-gradient(180deg, #111827 0%, #0b1221 100%)", "border": "#3b82f6", "text": "#f1f5f9", "tag": "BUILDER", "accent": "#3b82f6", "shadow": "rgba(59, 130, 246, 0.3)"},
        "researcher": {"bg": "radial-gradient(circle at center, #f4f4f5 0%, #ffffff 100%)", "border": "#18181b", "text": "#18181b", "tag": "RESEARCHER", "accent": "#18181b", "shadow": "rgba(0, 0, 0, 0.1)"},
        "designer": {"bg": "linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%)", "border": "#fb7185", "text": "#881337", "tag": "DESIGNER", "accent": "#fb7185", "shadow": "rgba(251, 113, 133, 0.2)"},
        "wizard": {"bg": "linear-gradient(180deg, #1e1b4b 0%, #312e81 100%)", "border": "#818cf8", "text": "#e0e7ff", "tag": "WIZARD", "accent": "#6366f1", "shadow": "rgba(99, 102, 241, 0.4)"},
        "ninja": {"bg": "linear-gradient(180deg, #0f172a 0%, #020617 100%)", "border": "#ef4444", "text": "#f87171", "tag": "NINJA", "accent": "#dc2626", "shadow": "rgba(220, 38, 38, 0.3)"},
        "architect": {"bg": "linear-gradient(180deg, #1c1917 0%, #0c0a09 100%)", "border": "#f59e0b", "text": "#fbbf24", "tag": "ARCHITECT", "accent": "#d97706", "shadow": "rgba(217, 119, 6, 0.3)"},
        "academic": {"bg": "linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%)", "border": "#64748b", "text": "#0f172a", "tag": "SCHOLAR", "accent": "#475569", "shadow": "rgba(71, 85, 105, 0.1)"},
        "legend": {"bg": "linear-gradient(180deg, #171717 0%, #0a0a0a 100%)", "border": "#a855f7", "text": "#f5f3ff", "tag": "LEGEND", "accent": "#8b5cf6", "shadow": "rgba(139, 92, 246, 0.5)"}
    }
    c = themes.get(theme_id, themes["builder"])

    html = f"""
    <!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&family=JetBrains+Mono:wght@700&display=swap' rel='stylesheet'>
    <script src='https://cdn.tailwindcss.com'></script>
    <style>
        body {{ font-family: 'Inter', sans-serif; margin: 0; display: flex; justify-content: center; align-items: flex-start; min-height: 100vh; background: transparent; overflow: hidden; }}
        .tag-font {{ font-family: 'JetBrains Mono', monospace; }}
        #github-dev-card {{ transform-origin: top center; }}
    </style></head>
    <body>
        <div id='github-dev-card' class='p-6 md:p-8 rounded-[2.5rem] md:rounded-[3rem] border-[4px] md:border-[6px]' style='background: {c['bg']}; border-color: {c['border']}; color: {c['text']}; width: 95%; max-width: 480px; position: relative; overflow: hidden; box-shadow: 0 0 40px {c['shadow']};'>
            <!-- Role Tag Badge -->
            <div class='absolute top-0 right-0 px-4 py-1.5 md:px-6 md:py-2 rounded-bl-2xl md:rounded-bl-3xl font-black tag-font text-[8px] md:text-[10px] tracking-[0.2em]' style='background: {c['accent']}; color: {"#fff" if theme_id in ["builder", "hacker", "cyberpunk", "wizard", "ninja", "architect", "legend"] else "#000"};'>
                {role_tag}
            </div>

            <div class='flex items-center gap-4 md:gap-6 mb-4 md:mb-6 mt-2'>
                <img src='{data['avatar']}' class='w-16 h-16 md:w-20 md:h-20 rounded-full border-2 md:border-4 shadow-2xl' style='border-color: {c['border']};' />
                <div class='min-w-0'>
                    <h2 class='text-xl md:text-2xl font-black uppercase tracking-tighter leading-none mb-1 truncate'>{data['name']}</h2>
                    <p class='text-xs md:text-sm font-bold opacity-60'>@{clean_name}</p>
                </div>
            </div>

            <p class='text-base md:text-lg italic font-medium mb-4 md:mb-6 leading-tight opacity-90'>"{vibe}"</p>

            <div class='grid grid-cols-2 gap-3 md:gap-4 mb-4 md:mb-6'>
                <div class='p-3 md:p-4 rounded-xl md:rounded-2xl border' style='background: rgba(128,128,128,0.05); border-color: rgba(128,128,128,0.1);'>
                    <span class='block text-[8px] md:text-[10px] font-black uppercase tracking-widest mb-2 opacity-50 tag-font'>Attributes</span>
                    {"".join([f'<div class="flex justify-between text-[10px] md:text-[11px] font-bold mb-1"><span class="opacity-70">{k}</span><span class="tag-font">{v}</span></div>' for k,v in rpg.items()])}
                </div>
                <div class='p-3 md:p-4 rounded-xl md:rounded-2xl border flex flex-col justify-center' style='background: rgba(128,128,128,0.05); border-color: rgba(128,128,128,0.1);'>
                    <span class='block text-[8px] md:text-[10px] font-black uppercase tracking-widest mb-1 opacity-30 tag-font italic text-center'>AI Roast</span>
                    <p class='text-[10px] md:text-[12px] font-bold italic leading-snug text-center'>"{roast}"</p>
                </div>
            </div>

            <div class='flex flex-wrap justify-center gap-2 mb-4 md:mb-6'>
                {"".join([f'<span class="px-2 py-0.5 md:px-3 md:py-1 text-[7px] md:text-[8px] font-black uppercase border-2 rounded-full tag-font" style="border-color: {c["border"]}">{s}</span>' for s in skills])}
            </div>

            <div class='flex justify-between text-[8px] md:text-[10px] font-black uppercase tracking-[0.2em] md:tracking-[0.3em] opacity-40 tag-font'>
                <span>{data.get('streak', 0)} DAY STREAK</span>
                <span>★ {data.get('total_repos', 0)} REPOS</span>
            </div>

            <div id='act-bar' class='mt-4 md:mt-6 pt-4 md:pt-5 border-t-2 flex' style='border-color: rgba(128,128,128,0.1);'>
                <button onclick='window.parent.downloadPNG()' class='flex-1 p-2 md:p-3 rounded-lg md:rounded-xl font-black text-[9px] md:text-[10px] uppercase tracking-widest hover:opacity-80 transition shadow-lg' style='background: {c['accent']}; color: {"#fff" if theme_id in ["builder", "hacker", "cyberpunk", "wizard", "ninja", "architect", "legend"] else "#000"};'>Download Identity File</button>
            </div>
        </div>
    </body></html>
    """
    file_path = os.path.join(CARDS_DIR, f"{clean_name}.html")
    with open(file_path, "w", encoding="utf-8") as f: f.write(html)
    return {"url": f"/static/cards/{clean_name}.html", "html": html, "theme": theme_id.upper()}

if __name__ == "__main__":
    mcp.run()

