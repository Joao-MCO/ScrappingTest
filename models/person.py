from sqlalchemy import Column, Integer, String, Date
from models.base import Base
from datetime import datetime

class Person(Base):
    __tablename__ = 'persons'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    nationality = Column(String)
    date_of_birth = Column(Date, nullable=True) 
    
    type = Column(String) 

    __mapper_args__ = {
        'polymorphic_identity': 'person',
        'polymorphic_on': type
    }

    def __init__(self, infos):
        self.id = infos['id']
        self.name = infos['name']
        self.nationality = infos.get('country', {}).get('name')
        
        ts = infos.get('dateOfBirthTimestamp')
        if ts:
            self.date_of_birth = datetime.fromtimestamp(ts).date()

    def to_dict(self):
        return {
            "id": self.id, 
            "name": self.name, 
            "nationality": self.nationality,
            "date_of_birth": str(self.date_of_birth) if self.date_of_birth else None
        }