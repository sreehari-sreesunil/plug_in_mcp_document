
# weather_mcp_client.py (Adapted for IDP)

import asyncio
import os
import base64
from google import genai
from google.genai import types
from fastmcp import Client

REMOTE_SERVER_URL = "http://localhost:8000/mcp"

async def upload_doc(mcp_client, filepath: str):
    """Helper to upload a file to the MCP server."""
    if not os.path.exists(filepath):
        print(f"Error: File '{filepath}' not found.")
        return None
    
    try:
        with open(filepath, "rb") as f:
            content = base64.b64encode(f.read()).decode('utf-8')
            
        filename = os.path.basename(filepath)
        print(f"Uploading {filename}...")
        
        result = await mcp_client.call_tool("upload_document", {
            "filename": filename,
            "file_content_base64": content
        })
        
        # Check result
        if result.content:
            print(f"Server response: {result.content[0].text}")
            print("NOTE: This document is now saved on the server and can be accessed via Option 2 next time.")
        
        return filename
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

async def main():
   
    mcp_client = Client(REMOTE_SERVER_URL)
    
    # Initialize connection
    async with mcp_client:
        await mcp_client.initialize()

        print("\n--- Intelligent Document Processing Client (Gemini) ---")
        
        # 0. Pre-fetch Context (Templates, Checklists)
        # This helps the LLM know what "v1" IDs are available without asking.
        print("Fetching system configuration...")
        try:
            templates_res = await mcp_client.read_resource("config://templates")
            rubrics_res = await mcp_client.read_resource("config://rubrics")
            checklists_res = await mcp_client.read_resource("config://checklists")
            questions_res = await mcp_client.read_resource("config://questions")
            
            system_context_str = (
                f"Available Templates: {templates_res[0].text}\n"
                f"Available Rubrics: {rubrics_res[0].text}\n"
                f"Available Checklists: {checklists_res[0].text}\n"
                f"Available Question Banks: {questions_res[0].text}\n"
            )
        except Exception as e:
            print(f"Warning: Could not fetch system config: {e}")
            system_context_str = "System config unavailable."

        print("1. Upload a document")
        print("2. Use existing server document")
        
        choice = input("Choose option (1/2): ")
        doc_id = None
        
        if choice == "1":
            file_path = input("Enter local file path: ")
            doc_id = await upload_doc(mcp_client, file_path)
            if not doc_id:
                return

        elif choice == "2":
            print("\nUpdating document list from server...")
            try:
                result = await mcp_client.read_resource("documents://list")
                print(f"Available documents: {result[0].text}")
                doc_id = input("Enter document ID from above: ")
            except Exception as e:
                print(f"Error listing documents: {e}")
                return
        
        else:
            print("Invalid choice.")
            return

        if not doc_id:
            print("No document selected.")
            return

        # Initialize Gemini client
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: GEMINI_API_KEY environment variable not set.")
            return
            
        gemini = genai.Client(api_key=api_key)

        print("\n--- Context Loading ---")
        user_prompt = input(f"\nWhat would you like to do with '{doc_id}'? (e.g., 'Assess the risk', 'Generate a checklist'): ")

        history = [
            types.Content(
                role="user", 
                parts=[
                    types.Part(
                        text=(
                            f"You are an expert Document Processor. You have access to tools to extract text, "
                            f"identify risks, and generate action checklists for document '{doc_id}'. \n"
                            "Always use the provided tools to answer questions. \n"
                            "When invoking tools like 'summarize_sections' or 'generate_action_checklist', "
                            "automatically select the most appropriate 'template_id' or 'checklist_id' from the Available Configs below "
                            "based on the document type (e.g., use 'loan_application' for loans, 'medical' for medical records). "
                            "Do not ask the user for IDs if a reasonable default exists in the config. \n\n"
                            f"Reliable document ID to use in tool calls: {doc_id}\n\n"
                            f"--- AVAILABLE CONFIGS ---\n{system_context_str}"
                        )
                    )
                ]
            ),
            types.Content(
                role="user",
                parts=[types.Part(text=user_prompt)]
            )
        ]

        gemini_tools = [mcp_client.session]

        print("\n🔵 Starting Gemini + MCP tool execution... (Type 'exit' to quit)")

        while True:
            try:
                # Call Gemini
                response = await gemini.aio.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=history,
                    config=types.GenerateContentConfig(tools=gemini_tools)
                )

                # Final Answer
                if response.text:
                    print("\n🟢 Gemini:", response.text)
                    
                    # Append to history
                    history.append(types.Content(role="model", parts=[types.Part(text=response.text)]))

                # Tool Calls
                if response.function_calls:
                    # Append tool call request to history
                    history.append(
                        types.Content(
                            role="model",
                            parts=[types.Part.from_function_call(fc) for fc in response.function_calls]
                        )
                    )

                    for fc in response.function_calls:
                        tool_name = fc.name
                        tool_args = dict(fc.args)

                        print(f"\n🤖 Gemini calls tool: {tool_name}")
                        print(f"Args: {tool_args}")

                        # Execute MCP tool
                        result = await mcp_client.call_tool(tool_name, tool_args)
                        
                        result_text = result.content[0].text if result.content else "No content returned."
                        print(f"   ➜ Tool Result: {result_text[:100]}...") 

                        # Append tool response to history
                        history.append(
                            types.Content(
                                role="function",
                                parts=[
                                    types.Part.from_function_response(
                                        name=tool_name,
                                        response={"result": result_text}
                                    )
                                ]
                            )
                        )
                    
                    # Continue generation automatically to get the final answer after tool usage
                    continue 

                # User Input Loop
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

            except Exception as e:
                print(f"Error during interaction loop: {e}")
                break

if __name__ == "__main__":
    asyncio.run(main())
