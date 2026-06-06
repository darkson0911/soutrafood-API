from datetime import datetime
from typing import List, Optional

from sqlalchemy import Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Classe de base pour la déclaration des modèles
class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom_complet: Mapped[str] = mapped_column(String)
    telephone: Mapped[str] = mapped_column(String, unique=True, index=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String)

    # Relation : Un utilisateur peut avoir plusieurs commandes
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    
    # Relations pour le Coin des Voisins
    community_meals: Mapped[List["CommunityMeal"]] = relationship("CommunityMeal", back_populates="user")
    community_orders: Mapped[List["CommunityOrder"]] = relationship("CommunityOrder", back_populates="user")


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nom: Mapped[str] = mapped_column(String)
    adresse: Mapped[str] = mapped_column(String)
    telephone_gerant: Mapped[str] = mapped_column(String)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relation : Un magasin peut proposer plusieurs paniers (boxes)
    boxes: Mapped[List["Box"]] = relationship("Box", back_populates="store")


class Box(Base):
    __tablename__ = "boxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.id"))
    titre: Mapped[str] = mapped_column(String)
    photo_base64: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    prix_original: Mapped[int] = mapped_column(Integer)  # En FCFA
    prix_reduit: Mapped[int] = mapped_column(Integer)  # En FCFA
    quantite_dispo: Mapped[int] = mapped_column(Integer)
    heure_recuperation: Mapped[str] = mapped_column(String)

    # Relation : Un panier appartient à un magasin
    store: Mapped["Store"] = relationship("Store", back_populates="boxes")
    
    # Relation : Un panier peut être commandé plusieurs fois
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="box")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    box_id: Mapped[int] = mapped_column(Integer, ForeignKey("boxes.id"))
    date_commande: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    statut: Mapped[str] = mapped_column(String, default="en_attente")
    code_validation: Mapped[str] = mapped_column(String(6), index=True)
    note: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relation : Une commande appartient à un utilisateur
    user: Mapped["User"] = relationship("User", back_populates="orders")
    
    # Relation : Une commande correspond à un panier spécifique
    box: Mapped["Box"] = relationship("Box", back_populates="orders")


class CommunityMeal(Base):
    __tablename__ = "community_meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    titre: Mapped[str] = mapped_column(String)
    photo_base64: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    quantite_dispo: Mapped[int] = mapped_column(Integer)
    zone: Mapped[str] = mapped_column(String)
    adresse_exacte: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_fermeture: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="community_meals")
    orders: Mapped[List["CommunityOrder"]] = relationship("CommunityOrder", back_populates="meal")


class CommunityOrder(Base):
    __tablename__ = "community_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    meal_id: Mapped[int] = mapped_column(Integer, ForeignKey("community_meals.id"))
    code_validation: Mapped[str] = mapped_column(String(6), index=True)

    # Relations
    user: Mapped["User"] = relationship("User", back_populates="community_orders")
    meal: Mapped["CommunityMeal"] = relationship("CommunityMeal", back_populates="orders")
