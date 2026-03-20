from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from models.manager import Manager

class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    city = Column(String)
    country = Column(String)
    color_primary = Column(String)
    color_secondary = Column(String)
    
    manager_id = Column(Integer, ForeignKey('persons.id'))
    manager = relationship("Manager")

    def __init__(self, infos):
        self.id = infos['id']
        self.name = infos['name']
        self.city = infos.get('venue', {}).get('city', {}).get('name')
        self.country = infos['country']['name']
        self.color_primary = infos['teamColors']['primary']
        self.color_secondary = infos['teamColors']['secondary']
        
        if 'manager' in infos:
            self.manager = Manager(infos['manager'])