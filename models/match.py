from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from models.referee import Referee
from models.team import Team
from models.competition import Competition

class Match(Base):
    __tablename__ = 'matches'

    id = Column(Integer, primary_key=True)
    year = Column(String)
    round = Column(String)
    stadium = Column(String)
    city = Column(String)
    
    home_score = Column(Integer)
    away_score = Column(Integer)

    competition_id = Column(Integer, ForeignKey('competitions.id'))
    referee_id = Column(Integer, ForeignKey('persons.id'))
    home_team_id = Column(Integer, ForeignKey('teams.id'))
    away_team_id = Column(Integer, ForeignKey('teams.id'))

    competition = relationship("Competition")
    referee = relationship("Referee")
    home_team = relationship("Team", foreign_keys=[home_team_id])
    away_team = relationship("Team", foreign_keys=[away_team_id])

    def __init__(self, event):
        self.id = event['id']
        self.year = event['season']['year']
        
        round_info = event.get('roundInfo', {})
        
        round_name = round_info.get('name')
        
        if not round_name:
            round_number = round_info.get('round')
            if round_number is not None:
                round_name = f"Round {round_number}"
            else:
                round_name = "Desconhecida"
                
        self.round = round_name
        self.stadium = event['venue']['name']
        self.city = event['venue']['city']['name']
        
        self.home_score = event['homeScore']['current']
        self.away_score = event['awayScore']['current']

        self.competition = Competition(event['tournament'])
        self.referee = Referee(event['referee'])
        self.home_team = Team(event['homeTeam'])
        self.away_team = Team(event['awayTeam'])