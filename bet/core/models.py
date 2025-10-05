from datetime import date, time

from pydantic import BaseModel


class Partida(BaseModel):
    evento_id: str
    data: date
    hora: time
    home_team: str
    away_team: str


class Tournament(BaseModel):
    name: str
    category: dict


class Status(BaseModel):
    description: str
    type: str


class HomeTeam(BaseModel):
    name: str
    slug: str
    shortName: str | None = None


class AwayTeam(BaseModel):
    name: str
    slug: str
    shortName: str | None = None


class HomeScore(BaseModel):
    current: int | None = None


class AwayScore(BaseModel):
    current: int | None = None


class Event(BaseModel):
    tournament: Tournament
    status: Status
    homeTeam: HomeTeam
    awayTeam: AwayTeam
    homeScore: HomeScore
    awayScore: AwayScore
    startTimestamp: int
    id: int

    def __eq__(self, other):
        return isinstance(other, Event) and self.id == other.id

    def __hash__(self):
        return hash(self.id)


class ScheduledEvent(BaseModel):
    tournament: Tournament
    status: Status
    homeTeam: HomeTeam
    awayTeam: AwayTeam
    id: int
    startTimestamp: int
    homeScore: HomeScore | None = None
    awayScore: AwayScore | None = None
    customId: str | None = None
    slug: str | None = None
