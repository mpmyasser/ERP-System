from core.db_manager import DBManager
from core.auth_models import SystemPermission

db = DBManager()
session = db.get_session()
permissions = session.query(SystemPermission).all()
for p in permissions:
    print(f"ID: {p.id}, Name: {p.name}, Description: {p.description}, Category: {p.category}")
session.close()
