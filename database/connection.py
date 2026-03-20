import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base

from models.competition import Competition
from models.person import Person
from models.player import Player
from models.manager import Manager
from models.referee import Referee
from models.team import Team
from models.match import Match
from models.teamstats import MatchTeamStat
from models.playerstats import PlayerStats

load_dotenv()
DATABASE_URL = os.getenv("NEONDB_URL")
DATABASE_USER = os.getenv("NEONDB_USER")
DATABASE_PWD = os.getenv("NEONDB_PWD")

engine = create_engine(f"postgresql://{DATABASE_USER}:{DATABASE_PWD}@{DATABASE_URL}?sslmode=require&channel_binding=require", echo=False)

def init_db():
    """Cria todas as tabelas no NeonDB se elas ainda não existirem."""
    Base.metadata.create_all(engine)
    print("🗄️ Tabelas do PostgreSQL (NeonDB) verificadas/criadas com sucesso!")

SessionLocal = sessionmaker(bind=engine)

def get_session():
    return SessionLocal()