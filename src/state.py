from typing import TypedDict , List , Dict ,Any ,Optional

class AgentState(TypedDict):
    resume_text: str                # Texte du CV extrait
    companies_list: List[Dict[str, Any]]  # Liste de toutes les entreprises du CSV
    current_index: int              # Index de l'entreprise en cours de traitement
    current_company: Optional[Dict[str, Any]] # Données de l'entreprise actuelle
    generated_subject: str          # Objet du mail généré
    generated_body: str             # Corps du mail généré
    user_decision: str              # Choix de l'utilisateur ("send", "skip", "terminate")
       