from datetime import date, time
from typing import Dict
from pydantic import BaseModel


class Partida(BaseModel):
    evento_id: str
    data: date
    hora: time
    home_team: str
    away_team: str

class Tournament(BaseModel):
    name: str
    category: Dict

class Status(BaseModel):
    description: str
    type: str

class HomeTeam(BaseModel):
    name: str
    slug: str
    shortName: str
    
class AwayTeam(BaseModel):
    name: str
    slug: str
    shortName: str

class HomeScore(BaseModel):
    current: int

class AwayScore(BaseModel):
    current: int

class Event(BaseModel):
    tournament: Tournament
    status: Status
    homeTeam: HomeTeam
    awayTeam: AwayTeam
    homeScore: HomeScore
    awayScore: AwayScore
    id: int

    def __eq__(self, other):
        return isinstance(other, Event) and self.id == other.id

    def __hash__(self):
        return hash(self.id)

