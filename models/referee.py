from sqlalchemy import Column, Integer
from models.person import Person

class Referee(Person):
    __mapper_args__ = {
        'polymorphic_identity': 'referee',
    }

    games = Column(Integer, nullable=True)
    yellows = Column(Integer, nullable=True)
    reds = Column(Integer, nullable=True)

    def __init__(self, infos):
        super().__init__(infos)
        
        self.games = infos.get('games')
        self.yellows = infos.get('yellowCards')
        self.reds = infos.get('redCards')

    def __repr__(self):
        return f"<Referee id={self.id}, name={self.name}, games={self.games}>"