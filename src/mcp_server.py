from fastmcp import FastMCP
from llama_index.tools.google import GmailToolSpec
from dotenv import load_dotenv
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

