from fastmcp import FastMCP
import re
import json
from config_loader import get_templates, get_rubrics, get_schema, get_template, get_rubric
from document_processor import processor

mcp = FastMCP("idp-server")

# --- Resources ---

@mcp.resource("documents://list")
def list_documents() -> str:
    """List available documents in the system."""
    docs = processor.list_documents()
    return json.dumps(docs, indent=2)

@mcp.resource("config://templates")
def list_templates() -> str:
    """List available extraction templates."""
    return json.dumps(get_templates(), indent=2)

@mcp.resource("config://rubrics")
def list_rubrics() -> str:
    """List available risk rubrics."""
    return json.dumps(get_rubrics(), indent=2)

@mcp.resource("config://schemas/{schema_name}")
def get_output_schema(schema_name: str) -> str:
    """Get a specific output schema by name (e.g., loan_output)."""
    schema = get_schema(schema_name)
    if schema:
        return json.dumps(schema, indent=2)
    return "Schema not found."

# --- Tools ---

@mcp.tool()
def extract_document(document_id: str) -> str:
    """
    Extract raw text from a document.
    Args:
        document_id: The filename of the document (e.g., 'loan_app.pdf').
    """
    try:
        text = processor.extract_text(document_id)
        return text
    except FileNotFoundError:
        return f"Error: Document '{document_id}' not found."
    except Exception as e:
        return f"Error extracting document: {str(e)}"

@mcp.tool()
def summarize_sections(document_id: str, template_id: str) -> str:
    """
    Extract sections from a document based on a template for summarization.
    Args:
        document_id: The filename of the document.
        template_id: The ID of the template to use (e.g., 'loan_application_v1').
    """
    text = processor.extract_text(document_id)
    if text.startswith("Error"):
        return text
    
    template = get_template(template_id)
    if not template:
        return f"Error: Template '{template_id}' not found."
    
    # Simple regex based extraction based on template 'extraction_rules'
    # In a real app, this might be more sophisticated layout analysis
    extracted_data = {}
    
    # Iterate over rules to find content
    if 'extraction_rules' in template:
        for rule in template['extraction_rules']:
            field = rule.get('field')
            pattern = rule.get('pattern')
            if field and pattern:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Capture the first group if available, else the whole match
                    val = match.group(1) if match.groups() else match.group(0)
                    extracted_data[field] = val.strip()
    
    return json.dumps({
        "document_id": document_id,
        "template_id": template_id,
        "extracted_sections": extracted_data,
        "raw_text_snippet": text[:500] + "..." # Context
    }, indent=2)

@mcp.tool()
def identify_risks(document_id: str, rubric_id: str = "loan_risk_v1") -> str:
    """
    Identify potential risks in a document based on a risk rubric.
    Args:
        document_id: The filename of the document.
        rubric_id: The ID of the rubric to use (default: loan_risk_v1).
    """
    text = processor.extract_text(document_id).lower()

    if text.startswith("Error"):
        return text

    rubric = get_rubric(rubric_id)
    if not rubric:
        return f"Error: Rubric '{rubric_id}' not found."

    identified_risks = []
    
    # Very basic keyword matching for demonstration
    # Real logic would likely involve LLM calls or complex rules
    for criteria in rubric.get('criteria', []):
        risk_id = criteria.get('id')
        description = criteria.get('description', '').lower()
        
        # Heuristic: check if keywords from description appear in text 
        # (This is a simplified example)
        # In reality, this might check specific extracted fields values
        
        # For 'missing_info', we might check if 'signature' is absent
        if risk_id == 'missing_info' and 'signature' not in text:
            identified_risks.append({
                "id": risk_id,
                "level": criteria.get('risk_level'),
                "reason": "Potential missing signature."
            })
            
    return json.dumps({
        "document_id": document_id,
        "rubric_id": rubric_id,
        "risks": identified_risks
    }, indent=2)

@mcp.tool()
def generate_action_checklist(document_id: str) -> str:
    """
    Generate a checklist of actions based on document status.
    Args:
        document_id: The filename of the document.
    """
    # Placeholder logic
    return json.dumps([
        "Verify applicant identity",
        "Validate income proof",
        "Check credit score manually if < 600",
        "Confirm signature validity"
    ], indent=2)

if __name__ == "__main__":
    import uvicorn
    # mcp.run() handled by uvicorn usually, but fastmcp has a run method too
    print("Starting IDP MCP Server on port 8000...")
    mcp.run(transport="http", host="0.0.0.0", port=8000)
