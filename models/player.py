from sqlalchemy import Column, Integer, String
from models.person import Person

class Player(Person):
    """
    Representa um jogador, herdando atributos básicos de Person e 
    adicionando dados específicos de performance e mercado.
    """
    __mapper_args__ = {
        'polymorphic_identity': 'player',
    }

    height = Column(Integer, nullable=True)
    market_value = Column(Integer, nullable=True)
    primary_position = Column(String, nullable=True)

    def __init__(self, infos):
        super().__init__(infos)
        
        self.height = infos.get('height')
        self.primary_position = infos.get('position')
        
        market_value_raw = infos.get('proposedMarketValueRaw', {})
        self.market_value = market_value_raw.get('value')

    def __repr__(self):
        return f"<Player id={self.id}, name={self.name}, position={self.primary_position}>"