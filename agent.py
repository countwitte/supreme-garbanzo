import asyncio
from typing import List
from pydantic import Field
from pydantic_ai import Agent
from pydantic_ai.models.ollama import OllamaModel
from pydantic_ai.providers.ollama import OllamaProvider
from pydantic_ai.tools import Tool

from models import PlayerGrading, LeagueStanding
from scraper import ChessScotlandScraper


scraper = ChessScotlandScraper()

model = OllamaModel(
    model_name="gemma4:e4b-16k",
    provider=OllamaProvider(base_url="http://localhost:11434/v1"),
)


async def get_player_data(name: str = Field(description="Player name to search for")) -> PlayerGrading:
    result = await scraper.get_player_data(name)
    if result:
        return PlayerGrading(
            name=result.get("name", name),
            pnum=result.get("pnum", ""),
            standard_grade=result.get("standard_grade"),
            allegro_grade=result.get("allegro_grade"),
            club=result.get("club", ""),
        )
    return PlayerGrading(
        name=name,
        pnum="",
        standard_grade=None,
        allegro_grade=None,
        club="",
    )


async def get_league_results(
    league_query: str = Field(description="League name to search for, e.g., 'Central League', 'Glasgow League'")
) -> List[LeagueStanding]:
    results = await scraper.get_league_results(league_query)
    if results:
        return [
            LeagueStanding(
                rank=r["rank"],
                team_name=r["team_name"],
                played=r["played"],
                points=r["points"],
            )
            for r in results
        ]
    return []


system_prompt = """You are a Chess Scotland Specialist. You use Gemma 4's reasoning capabilities to navigate the legacy website. When a user asks for a player, you must first find their PNUM. When asked for league results, identify the correct year (2025-26) and division. Always output a clear Markdown table of results."""


agent = Agent(
    model=model,
    output_type=str,
    system_prompt=system_prompt,
    tools=[
        Tool(get_player_data, name="get_player_data"),
        Tool(get_league_results, name="get_league_results"),
    ],
)


async def run_query(query: str) -> str:
    result = await agent.run(query)
    return result.response


async def main():
    print("Chess Scotland AI Agent")
    print("Type 'quit' to exit\n")
    
    while True:
        query = input("Query: ").strip()
        
        if query.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        
        if not query:
            continue
        
        try:
            result = await run_query(query)
            print(f"\n{result}\n")
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())