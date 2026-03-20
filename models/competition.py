from sqlalchemy import Column, Integer, String
from models.base import Base

class Competition(Base):
    __tablename__ = 'competitions'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    primary_color = Column(String, nullable=True)
    secondary_color = Column(String, nullable=True)

    def __init__(self, tournament_data):
        """
        Recebe o bloco event['tournament'] do JSON.
        """
        unique_tourn = tournament_data.get('uniqueTournament', {})
        
        self.id = unique_tourn.get('id') or tournament_data.get('id')
        self.name = unique_tourn.get('name') or tournament_data.get('name')
        
        self.category = tournament_data.get('category', {}).get('name')
        self.primary_color = unique_tourn.get('primaryColorHex')
        self.secondary_color = unique_tourn.get('secondaryColorHex')

    def __repr__(self):
        return f"<Competition id={self.id}, name={self.name}>"