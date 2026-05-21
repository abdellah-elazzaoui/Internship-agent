import os
import asyncio
import pandas as pd
from fastmcp import Client
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessages
from fastmcp import Client
from src.state import AgentState

class AgentNode:
    def __init__(self):
        self.llm = ChatOllama(model="qwen2.5:3b",temperature=0)
        self.csv_file = os.path.abspath("../config/companies.csv")
        self.server_config = {
            "server":{
                "command":"python",
                "args":[os.path.abspath("./mcp_server.py")]
            }
        }
    def initialize_pipeline(self,state:AgentState)->dict:
        print("Chargement du registre initial des entreprises...")
        if not os.path.exists(self.csv_file):
            raise FileNotFoundError(f"File Not Found in {self.csv_file}")

        df = pd.read_csv(self.csv_file)
        return {
            "resume_text":"",
            "companies_list":df.to_dict(orient="records"),
            "current_index":0
        }
    
    def stage_next_company(self, state: AgentState) -> dict:
        if os.path.exists(self.csv_path):
            df = pd.read_csv(self.csv_path)
            companies_list = df.to_dict(orient="records")
        else:
            companies_list = state["companies_list"]
        idx = state["current_index"]
        if idx >= len(companies_list):
            return {"current_company": None, "companies_list": companies_list}
        return {
            "current_company": companies_list[idx], 
            "companies_list": companies_list,
            "user_decision": "pending"
        }
    
    def generate_personalized_email(self,state:AgentState):
        company = state["current_company"]
        print(f"\n[Classification] Analyse du profil de l'entreprise : {company['company_name']}...")
        # Step 1: Let the LLM intelligently match the target profile to a technical track
        classification_prompt = f"""
        Analyse la description de cette entreprise et choisis la meilleure catégorie.
        Options :
        - Réponds 'data' si l'offre concerne le Big Data, le SQL, le Data Engineering, les pipelines de streaming ou la Business Intelligence.
        - Réponds 'ai' si l'offre concerne le Machine Learning, les Agents IA, les LLMs, la Vision par Ordinateur ou le NLP.
        - Réponds 'both' si c'est une entreprise tech généraliste, une ESN, ou si elle couvre tous les domaines à la fois.
        
        Details du poste:
        Role : {company['role']}
        Résumé : {company['job_description_summary']}
        Format de sortie : Renvoie UNIQUEMENT l'un des mots suivants : 'data', 'ai', 'both'. Pas de ponctuation, pas de phrases.
        """
        topic_choice = self.llm.invoke([HumanMessages(content=classification_prompt)]).content.strip().lower()
        print(f"[Routeur] Sélection du CV spécialisé : '{topic_choice}'")
        # Step 2: Extract text from the corresponding resume using the FastMCP Client context
        async def fetch_resume_via_fastmcp():
            async with Client(self.server_config) as client:
                res = await client.call_tool(
                    name="get_specialized_resume",
                    arguments = {"topic":topic_choice}
                )
                return str(res),topic_choice

        resume_content, chosen_topic = asyncio.run(fetch_resume_via_fastmcp())    

        # Step 3: Draft the tailored PFA cold email
        print(f"[Rédaction] Génération de la candidature personnalisée...")
        pitch_prompt = """
        Tu es un expert en recrutement. Rédige un mail de motivation percutant en français pour une demande de stage PFA (Projet de Fin d'Année).
        
        MON CV EXTRAIT :
        {resume_content}

        DÉTAILS DE L'ENTREPRISE CIBLE :
        Entreprise : {company['company_name']} | Poste recherché : {company['role']}
        Contexte / Stack : {company['job_description_summary']}

        CONSIGNES :
        - Rédige un mail direct, professionnel et personnalisé d'environ 150 mots.
        - Fais un lien clair entre mes compétences clés (présentes dans le CV) et les besoins de l'entreprise.
        - Ne mets pas d'objet, génère uniquement le corps du texte. Pas de mise en forme markdown.
        """
        response = self.llm.invoke(HumanMessages(content=pitch_prompt))

        # Save track metadata back into company instance so file dispatcher drops the right binary asset
        company["matched_topic"] = chosen_topic
        return {
            "resume_text": resume_content,
            "generated_subject": f"Demande de Stage PFA - {company['role']}",
            "generated_body": response.content.strip(),
            "current_company": company
        }
    
    def human_review_checkpoint(self,state:AgentState) ->dict:
        company = state["current_company"]
        print(f"\n==================================================================")
        print(f"DESTINATAIRE : {company['recruiter_name']} ({company['contact_email']})")
        print(f"OBJET : {state['generated_subject']}\n")
        print(state["generated_body"])
        print(f"==================================================================")

        decision = input("Action : [S]envoyer avec PDF | [K]ip (Passer) | [T]erminer ").strip().lower()
        mapping = {"s": "send", "k": "skip", "t": "terminate"}
        return {"user_decision": mapping.get(decision, "skip")}
    
    def execute_mcp_email_dispatch(self,state:AgentState)->dict:
        company = state["current_company"]
        topic = company.get("matched_topic","both")
        filename_map = {"data":"Abdellah_CV_AI.pdf" , "ai":"Abdellah_CV_Data.pdf" , "both":"Abdellah_Elazzaoui_CV.pdf"}
        resolved_filename = filename_map.get(topic,"Abdellah_Elazzaoui_CV.pdf")

        print(f"Envoi du mail et du fichier {resolved_filename} via FastMCP...")

        async def run_dispatch_and_archive_pipeline():
            async with Client(self.server_config) as client:
                email_result = await client.call_tool(
                    name="create_and_send_with_attachment",
                    arguments = {
                        "to_email":company["contact_email"],
                        "subject":state['generated_subject'],
                        "body":state['generated_body'],
                        "resume_filename":resolved_filename
                    }
                )
                server_ouput = str(email_result)
                if "Success" in server_ouput:
                    migration_result = await client.call_tool(
                        name = "processed_company",
                        argumments={
                            "contact_email":company["contact_email"]
                        }
                    )
                    print(f"[Agent Tracking Engine] : {migration_result}")
        
        asyncio.run(run_dispatch_and_archive_pipeline())
        return {"current_index": state["current_index"]}
    
    def log_skip(self, state: AgentState) -> dict:
        print("[─] Entreprise ignorée. Enregistrement conservé intact dans companies.csv.")
        # Increment index pointer because row state was kept untouched in companies.csv
        return {"current_index": state["current_index"] + 1}


