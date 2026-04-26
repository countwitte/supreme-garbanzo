from pydantic import BaseModel, Field
from typing import Optional


class PlayerGrading(BaseModel):
    name: str
    pnum: str = Field(description="The unique Chess Scotland Player Number")
    standard_grade: Optional[int]
    allegro_grade: Optional[int]
    club: str


class LeagueStanding(BaseModel):
    rank: int
    team_name: str
    played: int
    points: float