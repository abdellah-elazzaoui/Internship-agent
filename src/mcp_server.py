from fastmcp import FastMCP
from fastmcp.exception import ToolError
from llama_index.tools.google import GmailToolSpec
from dotenv import load_dotenv
from pypdf import PdfReader
import datetime
import os

mcp = FastMCP(
    "internship_agent",
    instructions = "Provide Tool For Looging to PFA internship",
    on_duplicate = "error"
    )

#____________ Gmail _________________
gmail_spec = GmailToolSpec(
    credentials_path = "../config/credentials.json",
    token_path = "../config/mail_uiz_token.json"
)
gmail_tool_spec = gmail_spec.to_tool_list()


def register_llama_tools(tool_list: list, label: str):
    for tool in tool_list:
        fn = getattr(tool, "fn", None)
        if fn is None or not callable(fn):
            print(f"[{label}] [WARN] Could not extract function from tool {tool!r} — skipping.")
            continue
        tool_name = getattr(tool.metadata, "name", "unknown_tool")
        tool_description = getattr(tool.metadata, "description", "No description provided.")
        decorator = mcp.tool(name=tool_name, description=tool_description)
        decorator(fn)
        print(f"[{label}] Registered the tool: {tool_name}")    
    print("-" * 30)

register_llama_tools(gmail_tool_spec,"Gmail")


@mcp.tool(name="get_specialized_resume",description="Selects and reads the text of the correct resume based on a topic string ('data', 'ai', or 'both')")
def get_specialized_resume(topic:str):
    """Dynamically pathways into the correct resume directory file."""
    topic = str(topic).strip().lower()
    file_mapping = {
        "data": "../config/Abdellah_CV_Data.pdf",
        "ai": "../config/Abdellah_CV_AI.pdf",
        "both": "../config/Abdellah_Elazzaoui_CV.pdf"
    }
    target_path = file_mapping.get(topic,"../config/Abdellah_Elazzaoui_CV.pdf")
    if not os.path.exists(target_path):
        return ToolError(f"Error: Target resume file not found at path: {target_path}")
    try:
        reader = PdfReader(target_path)
        text = "".join([page.extract_text() + "\n" for page in reader.pages]).strip()
        return text
    except Exception as e:
        return f"Error parsing PDF file framework: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
