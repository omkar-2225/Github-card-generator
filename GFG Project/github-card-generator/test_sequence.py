import asyncio
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv(dotenv_path="backend/.env")

# Ensure the paths are correct for importing
import sys
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def test_end_to_end():
    from mcp_server import scrape_github, analyze_profile, generate_and_save_card

    username = "torvalds"
    print(f"--- Starting End-to-End Test for user: {username} ---")

    # 1. Scrape GitHub
    print("Step 1: Calling scrape_github...")
    github_data = await scrape_github(username)
    if "error" in github_data:
        print(f"ERROR in scrape_github: {github_data['error']}")
        return
    print("Success: GitHub data retrieved.")

    # 2. Analyze Profile
    print("Step 2: Calling analyze_profile...")
    analysis = await analyze_profile(github_data)
    if "error" in analysis:
        print(f"ERROR in analyze_profile: {analysis['error']}")
        return
    print("Success: Profile analyzed by Gemini.")

    # 3. Generate and Save Card
    print("Step 3: Calling generate_and_save_card...")
    try:
        result = await generate_and_save_card(username, github_data, analysis)
        print("Success: Card generated and saved.")
    except Exception as e:
        print(f"ERROR in generate_and_save_card: {str(e)}")
        return

    # 4. Print results
    print("\n--- TEST RESULTS ---")
    print(f"Card Theme: {analysis.get('theme')}")
    print(f"Developer Vibe: {analysis.get('vibe')}")
    print(f"Card URL: {result.get('url')}")
    print("\nFull Analysis JSON:")
    print(json.dumps(analysis, indent=2))

    print("\n--- Test Completed Successfully ---")

if __name__ == "__main__":
    asyncio.run(test_end_to_end())
