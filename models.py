from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Eleve(Base):
    __tablename__ = "eleves"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    groupe_id = Column(Integer, ForeignKey("groupes.id"))

class Groupe(Base):
    __tablename__ = "groupes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    taille = Column(Integer)
    eleves = relationship("Eleve", backref="groupe")
