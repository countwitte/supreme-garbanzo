from pydantic import BaseModel, Field
from typing import Optional


class PlayerGrading(BaseModel):
    name: str
    pnum: str = Field(description="The unique Chess Scotland Player Number")
    standard_grade: Optional[int] = None
    standard_grade_live: Optional[int] = None
    allegro_grade: Optional[int] = None
    allegro_grade_live: Optional[int] = None
    club: str


class LeagueStanding(BaseModel):
    rank: int
    team_name: str
    played: int
    points: float