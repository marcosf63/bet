"""Tests for bet.core.models module."""

from datetime import date, time

import pytest

from bet.core.models import (
    AwayScore,
    AwayTeam,
    Event,
    HomeScore,
    HomeTeam,
    Partida,
    ScheduledEvent,
    Status,
    Tournament,
)


class TestPartida:
    """Tests for Partida model."""

    def test_partida_creation(self):
        """Test creating a Partida instance."""
        partida = Partida(
            evento_id="12345",
            data=date(2024, 12, 25),
            hora=time(15, 30),
            home_team="Team A",
            away_team="Team B",
        )
        assert partida.evento_id == "12345"
        assert partida.data == date(2024, 12, 25)
        assert partida.hora == time(15, 30)
        assert partida.home_team == "Team A"
        assert partida.away_team == "Team B"

    def test_partida_validation(self):
        """Test Partida validation."""
        with pytest.raises(Exception):
            Partida(
                evento_id="12345",
                data="invalid-date",
                hora=time(15, 30),
                home_team="Team A",
                away_team="Team B",
            )


class TestTournament:
    """Tests for Tournament model."""

    def test_tournament_creation(self):
        """Test creating a Tournament instance."""
        tournament = Tournament(name="Premier League", category={"name": "England", "id": 1})
        assert tournament.name == "Premier League"
        assert tournament.category["name"] == "England"
        assert tournament.category["id"] == 1


class TestStatus:
    """Tests for Status model."""

    def test_status_creation(self):
        """Test creating a Status instance."""
        status = Status(description="Not started", type="notstarted")
        assert status.description == "Not started"
        assert status.type == "notstarted"


class TestTeams:
    """Tests for HomeTeam and AwayTeam models."""

    def test_home_team_creation(self):
        """Test creating a HomeTeam instance."""
        team = HomeTeam(name="Manchester United", slug="manchester-united")
        assert team.name == "Manchester United"
        assert team.slug == "manchester-united"
        assert team.shortName is None

    def test_home_team_with_short_name(self):
        """Test creating a HomeTeam with short name."""
        team = HomeTeam(name="Manchester United", slug="manchester-united", shortName="Man Utd")
        assert team.shortName == "Man Utd"

    def test_away_team_creation(self):
        """Test creating an AwayTeam instance."""
        team = AwayTeam(name="Liverpool", slug="liverpool", shortName="LFC")
        assert team.name == "Liverpool"
        assert team.slug == "liverpool"
        assert team.shortName == "LFC"


class TestScores:
    """Tests for HomeScore and AwayScore models."""

    def test_home_score_none(self):
        """Test HomeScore with no current score."""
        score = HomeScore()
        assert score.current is None

    def test_home_score_with_value(self):
        """Test HomeScore with current score."""
        score = HomeScore(current=2)
        assert score.current == 2

    def test_away_score_none(self):
        """Test AwayScore with no current score."""
        score = AwayScore()
        assert score.current is None

    def test_away_score_with_value(self):
        """Test AwayScore with current score."""
        score = AwayScore(current=1)
        assert score.current == 1


class TestEvent:
    """Tests for Event model."""

    def test_event_creation(self):
        """Test creating an Event instance."""
        event = Event(
            tournament=Tournament(name="Premier League", category={"name": "England", "id": 1}),
            status=Status(description="Not started", type="notstarted"),
            homeTeam=HomeTeam(name="Team A", slug="team-a"),
            awayTeam=AwayTeam(name="Team B", slug="team-b"),
            homeScore=HomeScore(current=0),
            awayScore=AwayScore(current=0),
            startTimestamp=1640430600,
            id=123456,
        )
        assert event.id == 123456
        assert event.homeTeam.name == "Team A"
        assert event.awayTeam.name == "Team B"
        assert event.startTimestamp == 1640430600

    def test_event_equality(self):
        """Test Event equality based on ID."""
        event1 = Event(
            tournament=Tournament(name="Premier League", category={"name": "England", "id": 1}),
            status=Status(description="Not started", type="notstarted"),
            homeTeam=HomeTeam(name="Team A", slug="team-a"),
            awayTeam=AwayTeam(name="Team B", slug="team-b"),
            homeScore=HomeScore(),
            awayScore=AwayScore(),
            startTimestamp=1640430600,
            id=123456,
        )
        event2 = Event(
            tournament=Tournament(name="La Liga", category={"name": "Spain", "id": 2}),
            status=Status(description="In progress", type="inprogress"),
            homeTeam=HomeTeam(name="Team C", slug="team-c"),
            awayTeam=AwayTeam(name="Team D", slug="team-d"),
            homeScore=HomeScore(),
            awayScore=AwayScore(),
            startTimestamp=1640440000,
            id=123456,  # Same ID
        )
        assert event1 == event2

    def test_event_inequality(self):
        """Test Event inequality with different IDs."""
        event1 = Event(
            tournament=Tournament(name="Premier League", category={"name": "England", "id": 1}),
            status=Status(description="Not started", type="notstarted"),
            homeTeam=HomeTeam(name="Team A", slug="team-a"),
            awayTeam=AwayTeam(name="Team B", slug="team-b"),
            homeScore=HomeScore(),
            awayScore=AwayScore(),
            startTimestamp=1640430600,
            id=123456,
        )
        event2 = Event(
            tournament=Tournament(name="Premier League", category={"name": "England", "id": 1}),
            status=Status(description="Not started", type="notstarted"),
            homeTeam=HomeTeam(name="Team A", slug="team-a"),
            awayTeam=AwayTeam(name="Team B", slug="team-b"),
            homeScore=HomeScore(),
            awayScore=AwayScore(),
            startTimestamp=1640430600,
            id=789012,  # Different ID
        )
        assert event1 != event2

    def test_event_hash(self):
        """Test Event hash based on ID."""
        event = Event(
            tournament=Tournament(name="Premier League", category={"name": "England", "id": 1}),
            status=Status(description="Not started", type="notstarted"),
            homeTeam=HomeTeam(name="Team A", slug="team-a"),
            awayTeam=AwayTeam(name="Team B", slug="team-b"),
            homeScore=HomeScore(),
            awayScore=AwayScore(),
            startTimestamp=1640430600,
            id=123456,
        )
        assert hash(event) == hash(123456)


class TestScheduledEvent:
    """Tests for ScheduledEvent model."""

    def test_scheduled_event_creation(self):
        """Test creating a ScheduledEvent instance."""
        event = ScheduledEvent(
            tournament=Tournament(name="Champions League", category={"name": "Europe", "id": 3}),
            status=Status(description="Scheduled", type="notstarted"),
            homeTeam=HomeTeam(name="Real Madrid", slug="real-madrid"),
            awayTeam=AwayTeam(name="Barcelona", slug="barcelona"),
            id=999888,
            startTimestamp=1640550000,
        )
        assert event.id == 999888
        assert event.homeTeam.name == "Real Madrid"
        assert event.awayTeam.name == "Barcelona"
        assert event.homeScore is None
        assert event.awayScore is None

    def test_scheduled_event_with_optional_fields(self):
        """Test ScheduledEvent with optional fields."""
        event = ScheduledEvent(
            tournament=Tournament(name="Champions League", category={"name": "Europe", "id": 3}),
            status=Status(description="Scheduled", type="notstarted"),
            homeTeam=HomeTeam(name="Real Madrid", slug="real-madrid"),
            awayTeam=AwayTeam(name="Barcelona", slug="barcelona"),
            id=999888,
            startTimestamp=1640550000,
            homeScore=HomeScore(current=0),
            awayScore=AwayScore(current=0),
            customId="custom-123",
            slug="real-madrid-vs-barcelona",
        )
        assert event.homeScore.current == 0
        assert event.awayScore.current == 0
        assert event.customId == "custom-123"
        assert event.slug == "real-madrid-vs-barcelona"
