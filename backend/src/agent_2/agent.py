"""
Agent 2 - Analyse d'impact (prototype base sur l'agent ReAct).
"""

from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI

from src.agent_2.prompts.agent_2_prompt import AGENT_2_PROMPT
from src.agent_2.tools import get_agent_2_tools
from src.config import settings


class Agent2:
    """
    Agent 2 - Analyse d'impact et recommandations.

    Version prototype: recuperation des analyses via outil.
    """

    def __init__(self):
        if not settings.google_api_key:
            raise ValueError(
                "GOOGLE_API_KEY renseigné dans .env"
            )

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            api_key=settings.google_api_key,
            temperature=0,
        )

        tools = get_agent_2_tools()

        self.agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=AGENT_2_PROMPT,
            debug=False,
        )

    def run(self, validation_status: str = "approved", limit: int = 5):
        """
        Recupere les analyses et renvoie une synthese.
        """
        task = (
            "Recupere les analyses depuis la base de donnees "
            f"avec validation_status='{validation_status}' et limite {limit}."
        )
        return self.agent.invoke({"messages": [{"role": "user", "content": task}]})

    def analyze_impact(self, analysis_id: str):
        """
        Recupere une analyse precise par ID.
        """
        task = f"Recupere l'analyse avec analysis_id='{analysis_id}'."
        return self.agent.invoke({"messages": [{"role": "user", "content": task}]})


if __name__ == "__main__":
    agent = Agent2()
    result = agent.run()
    messages = result.get("messages", [])
    if messages:
        content = messages[-1].content
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            print("\n".join([t for t in text_parts if t]))
        else:
            print(content)
    else:
        print(result)
