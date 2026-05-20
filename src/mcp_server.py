from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fastmcp import FastMCP
from fastmcp.exception import ToolError
from llama_index.tools.google import GmailToolSpec
from dotenv import load_dotenv
from pypdf import PdfReader
import pandas as pd
import base64
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


@mcp.tool(name="processed_company",description="Removes a processed company from companies.csv by its contact email and moves it into checked.csv.")
def processed_company(contact_email:str):
    """Safely updates tracking spreadsheets to ensure no duplicated application emails are sent."""
    csv_path = os.path.abspath("../config/companies.csv")
    checked_path = os.path.abspath("../config/checked.csv")
    if not csv_path:
        return "Error: Source companies.csv file not found."
    
    try:
        data = data.read_csv(csv_path)
        target_row = data[data['contact_email']==contact_email]
        if not target_row:
            return f"Warning: Company with email {contact_email} was not found in the source list."
        
        if os.path.abspath(checked_path):
            target_row.to_csv(checked_path,mode="a",header=False,index=False)
        else:
            target_row.to_csv(checked_path,mode="w",header=True,index=False)
        df_updated = data[data['contact_email']!=contact_email]    
        df_updated.to_csv(csv_path,index=False)
        return f"Success: Moved entry for {contact_email} completely to checked.csv."
        
    except Exception as e:
        return f"CSV Tracking Engine Exception: {str(e)}"


#TOOL : TRUE BINARY GMAIL ATTACHMENT DISPATCHER
@mcp.tool(name="create_and_send_with_attachment",description="Constructs an authentic MIME Multipart application mail pack containing a raw uncorrupted physical PDF file, sending it directly via Gmail API contexts")
def create_and_send_with_attachment(to_email:str,subject:str,body:str,resume_filename:str):
    """Assembles structural file bytes and pushes base64 URL-encoded payload packages directly to user accounts."""
    file_path = os.path.abspath(f"../config/{resume_filename}")
    if not os.path.exists(file_path):
        return f"Error: Critical physical asset reference file missing: {resume_filename}"
    try:
        # Step A: Assemble standard Multi-part transactional container elements
        message = MIMEMultipart()
        message['to']=to_email
        message['subject']=subject
        # Attach plaintext presentation pitch
        message.attach(MIMEText(body,'plain'))
        # Step B: Read original raw binary stream contents and attach headers
        with open(file_path,"rb") as pdf_file:
            attachement = MIMEApplication(pdf_file.read() , _subtype='pdf')
            attachement.add_header("Content-Disposition",'attachment',filename=resume_filename)
            message.attach(attachement)
        # Step C: Convert physical transaction content strictly into standard base64 URL-safe parameters
        raw_base64 = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")   
        payload = {"raw":raw_base64}
        # Step D: Authenticate using LlamaIndex credential bindings and deliver package to endpoint
        gmail_service = gmail_spec()._get_credentials()
        gmail_service.users().messages().send(userId="me",body=payload).execute()
        return f"Success: Enterprise application profile dispatched completely to {to_email} containing physical file {resume_filename} attachment links."
    except Exception as e:
        return f"MIME Generation Fail / API Connection Exception: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
