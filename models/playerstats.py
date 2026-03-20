from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, JSON
from models.base import Base

class PlayerStats(Base):
    __tablename__ = 'player_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    match_id = Column(Integer, ForeignKey('matches.id'))
    player_id = Column(Integer, ForeignKey('persons.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))

    jersey_number = Column(String, nullable=True)
    position = Column(String, nullable=True)
    substitute = Column(Boolean, default=False)

    minutes_played = Column(Integer, default=0)
    rating = Column(Float, nullable=True)
    
    raw_stats = Column(JSON)

    def __init__(self, match_id, team_id, player_data):
        self.match_id = match_id
        self.team_id = team_id
        self.player_id = player_data['player']['id']
        
        self.jersey_number = player_data.get('jerseyNumber')
        self.position = player_data.get('position')
        self.substitute = player_data.get('substitute', False)
        
        stats = player_data.get('statistics', {})
        self.minutes_played = stats.get('minutesPlayed', 0)
        self.rating = stats.get('rating')
        
        self.raw_stats = stats

    @staticmethod
    def parse_lineups(lineups_json, match_id, home_team_id, away_team_id):
        """
        Recebe o JSON da aba 'lineups' e devolve uma lista de PlayerStats 
        pronta para ser enviada ao banco de dados.
        """
        player_stats_rows = []
        
        if 'home' in lineups_json and 'players' in lineups_json['home']:
            for p_data in lineups_json['home']['players']:
                if p_data.get('statistics', {}).get('rating'):
                    stat = PlayerStats(match_id, home_team_id, p_data)
                    player_stats_rows.append(stat)

        if 'away' in lineups_json and 'players' in lineups_json['away']:
            for p_data in lineups_json['away']['players']:
                if p_data.get('statistics', {}).get('rating'):
                    stat = PlayerStats(match_id, away_team_id, p_data)
                    player_stats_rows.append(stat)

        return player_stats_rows