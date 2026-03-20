from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from models.base import Base
from services.utils import parse_stat_value

class MatchTeamStat(Base):
    __tablename__ = 'match_team_stats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    team_id = Column(Integer, ForeignKey('teams.id'))
    stat_name = Column(String)
    value = Column(JSON)

    def __init__(self, match_id, team_id, stat_name, value):
        self.match_id = match_id
        self.team_id = team_id
        self.stat_name = stat_name
        self.value = value

    @staticmethod
    def parse_statistics(stats_json, match_id, home_team_id, away_team_id):
        """
        Lê o JSON gigante, ignora o 1º e 2º tempo, e retorna apenas
        as estatísticas do jogo completo prontas para o banco.
        """
        stat_rows = []
        
        full_match_stats = next((p for p in stats_json if p['period'] == 'ALL'), None)
        
        if not full_match_stats:
            return stat_rows

        for group in full_match_stats['groups']:
            for stat in group['statisticsItems']:
                stat_key = stat['key'] 
                
                home_val = parse_stat_value(stat['home'])
                away_val = parse_stat_value(stat['away'])
                
                stat_rows.append(MatchTeamStat(match_id, home_team_id, stat_key, home_val))
                stat_rows.append(MatchTeamStat(match_id, away_team_id, stat_key, away_val))
                
        return stat_rows