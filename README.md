# HAWCC

### Hebbale Academy Workspace for Coding on Cloud

# IDP MCP Server

A configuration-driven MCP (Microservice for Content Processing) server for Intelligent Document Processing. This server exposes document resources and processing tools, allowing LLM clients to validate, extract, and summarize document content based on swappable configuration rubrics.

## Features

- **Document Ingestion**: Upload PDF, DOCX, or TXT documents via tools or volume mounts.
- **Config-Driven**: Templates and extraction rules defined in YAML.
- **Tools Included**:
    - `extract_document`: Extract raw text.
    - `upload_document`: Client-side upload via Base64.
    - `summarize_sections`: Structured summarization based on templates.
    - `identify_risks`: Risk assessment based on rubrics.

## Prerequisites

- **Docker Desktop** (for containerized execution)
- **Python 3.11+** (for local execution or client testing)

## Installation & Setup

1. Clone the repository.
2. Ensure you have the necessary configuration files in `configs/` and data directories.

## Docker Usage (Recommended)

### 1. Build the Image

Run this command from the project root:

```powershell
docker build -t idp-server .
```

### 2. Run the Container

Run the following command to start the server. It mounts your local `data` and `configs` directories so changes persist and are visible.

```powershell
docker run --rm -p 8000:8000 -v ${PWD}/data:/app/data -v ${PWD}/configs:/app/configs idp-server
```

> **Note**: In Command Prompt (cmd), replace `${PWD}` with `%cd%`.

### 3. Verify Server

Check if the server is running by visiting:  
[http://localhost:8000/documents/list](http://localhost:8000/documents/list)

## Client Usage

The included `client.py` demonstrates how to connect to the MCP server, upload a file, and request analysis (optionally using Google Gemini if configured).

1. Install client dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the client:
   ```bash
   python client.py
   ```

