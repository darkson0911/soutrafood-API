from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# URL de connexion à la base de données SQLite pour l'environnement de développement local
SQLALCHEMY_DATABASE_URL = "sqlite:///./soutrafood_v2.db"

# Création du moteur de base de données (engine)
# L'argument connect_args={"check_same_thread": False} est obligatoire pour utiliser SQLite 
# avec FastAPI car FastAPI peut faire transiter des requêtes entre différents threads.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Création de la classe SessionLocal qui servira d'usine pour générer nos sessions de base de données
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Fonction génératrice permettant de gérer de manière sécurisée le cycle de vie de la session
# Elle servira de dépendance (Dependency Injection) dans nos routes FastAPI
def get_db():
    db = SessionLocal()
    try:
        # Transmet (yield) la session à la requête en cours
        yield db
    finally:
        # Assure la fermeture de la session à la fin de la requête, qu'elle ait réussi ou échoué
        db.close()
