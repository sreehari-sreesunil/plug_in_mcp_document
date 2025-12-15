import asyncio
import os

from google import genai
from google.genai import types
from fastmcp import Client

# ===============================
# Configuration
# ===============================
MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"
DOC_ID = "sample_loan.txt"  # Ensure this file exists in data/ dir for testing


async def main():
    print(f"Connecting to MCP Server at {MCP_SERVER_URL}...")

    # ===============================
    # Initialize Gemini Client
    # ===============================
    try:
        gemini = genai.Client(
            api_key=os.environ.get("AIzaSyAoB44GykvTfCY12hEoSOR-DD1Ib83kSOs")
        )
        print("Gemini client initialized")
    except Exception:
        print("GEMINI_API_KEY not found. Skipping LLM part.")
        gemini = None

    # ===============================
    # Initialize MCP Client
    # ===============================
    mcp_client = Client(MCP_SERVER_URL)

    async with mcp_client:
        await mcp_client.initialize()

        # ===============================
        # 1. List Templates (Resource)
        # ===============================
        print("\n--- Fetching Templates ---")
        templates = await mcp_client.read_resource("config://templates")
        print(templates[0].text)

        # ===============================
        # 2. Extract Document (Tool)
        # ===============================
        print(f"\n--- Extracting Document: {DOC_ID} ---")
        try:
            extraction = await mcp_client.call_tool(
                "extract_document",
                {"document_id": DOC_ID}
            )
            print(extraction.content[0].text[:200] + "...")
        except Exception as e:
            print(f"Extraction failed (expected if file missing): {e}")

        # ===============================
        # 3. Summarize Document (Tool)
        # ===============================
        print("\n--- Summarizing Document ---")
        try:
            summary = await mcp_client.call_tool(
                "summarize_sections",
                {
                    "document_id": DOC_ID,
                    "template_id": "loan_application_v1"
                }
            )
            print(summary.content[0].text)
        except Exception as e:
            print(f"Summarization failed: {e}")

        # ===============================
        # 4. Gemini Analysis
        # ===============================
        if gemini:
            print("\n--- Gemini Analysis ---")

            user_prompt = (
                "Analyze the risk of this loan application "
                "based on the extracted data."
            )

            # Register MCP tools for Gemini
            gemini_tools = [mcp_client.session]

            history = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=user_prompt)]
                )
            ]

            response = await gemini.aio.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=history,
                config=types.GenerateContentConfig(
                    tools=gemini_tools
                )
            )

            if response.text:
                print(f"Gemini Answer:\n{response.text}")
            elif response.function_calls:
                print(
                    f"Gemini wants to call tool: "
                    f"{response.function_calls[0].name}"
                )


if __name__ == "__main__":
    asyncio.run(main())
