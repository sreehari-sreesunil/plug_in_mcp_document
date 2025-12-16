
# weather_mcp_client.py (Adapted for IDP)

# Used to run asynchronous functions such as calling the MCP server and Gemini
import asyncio
import asyncio
import os
import base64 # Added for upload

# Main Google Gemini client used to interact with the model
from google import genai  

# Provides structured message types for prompting, history, and tool responses
from google.genai import types  

# FastMCP client used to connect to and call tools on the MCP server
from fastmcp import Client  

# URL of the remote MCP server where tools and resources are registered
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
        
        return filename
    except Exception as e:
        print(f"Upload failed: {e}")
        return None

async def main():
   
    mcp_client = Client(REMOTE_SERVER_URL)
    
    # Initialize connection
    async with mcp_client:
        await mcp_client.initialize()

        print("\n--- Intelligent Document Processing Client ---")
        print("1. Upload a document")
        print("2. Use existing server document")
        
        choice = input("Choose option (1/2): ")
        doc_id = None
        
        if choice == "1":
            file_path = input("Enter local file path: ")
            doc_id = await upload_doc(mcp_client, file_path)
            if not doc_id:
                print("Aborting.")
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
        # Optional: Load checklists or rubrics into context so Gemini knows the rules?
        # For now, we'll let Gemini discover them via tools or user prompt instructions.
        
        user_prompt = input(f"\nWhat would you like to do with '{doc_id}'? (e.g., 'Assess the risk', 'Generate a checklist'): ")

        # --------------------------------------------------
        # STEP 2: Initialize Gemini conversation with context
        # --------------------------------------------------
        
        history = [
            # 2.1 System-style context
            types.Content(
                role="user", 
                parts=[
                    types.Part(
                        text=(
                            f"You are an expert Document Processor. You have access to tools to extract text, "
                            f"identify risks, and generate action checklists for document '{doc_id}'. \n"
                            "Always use the provided tools to answer questions. \n"
                            "Reliable document ID to use in tool calls: " + doc_id
                        )
                    )
                ]
            ),
            # 2.2 Actual user question
            types.Content(
                role="user",
                parts=[types.Part(text=user_prompt)]
            )
        ]

        # 2.3 Register MCP session so Gemini can call MCP tools during generation
        gemini_tools = [mcp_client.session]

        print("\n🔵 Starting Gemini + MCP tool execution...")

        # --------------------------------------------------
        # STEP 3: Gemini Tool Chaining Loop
        # --------------------------------------------------
        while True:
            try:
                # 3.1. Call Gemini with the current history
                response = await gemini.aio.models.generate_content(
                    model="gemini-2.0-flash-exp",
                    contents=history,
                    config=types.GenerateContentConfig(tools=gemini_tools)
                )

                # 3.2. Final answer from Gemini
                if response.text:
                    print("\n🟢 Final Answer:")
                    print(response.text)
                    break

                # 3.3. Gemini requests a tool call
                if response.function_calls:
                    for fc in response.function_calls:
                        tool_name = fc.name
                        tool_args = dict(fc.args)

                        print(f"\n🤖 Gemini calls tool: {tool_name}")
                        print(f"Args: {tool_args}")

                        # Execute MCP tool
                        result = await mcp_client.call_tool(tool_name, tool_args)
                        
                        # Handle result content
                        result_text = ""
                        if result.content:
                            result_text = result.content[0].text
                        else:
                            result_text = "No content returned."

                        print(f"   ➜ Tool Result: {result_text[:100]}...") 

                        # 3.4. Add tool request to history (REQUIRED for Gemini API correct history)
                        history.append(
                            types.Content(
                                role="model",
                                parts=[types.Part.from_function_call(fc)]
                            )
                        )

                        # 3.5. Add tool response to history
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

                else:
                    print("\n⚠️ Loop ended unexpectedly (no text, no function calls).")
                    break
            except Exception as e:
                print(f"Error during interaction loop: {e}")
                break

# Entry point that runs the async main() function
if __name__ == "__main__":
    asyncio.run(main())
