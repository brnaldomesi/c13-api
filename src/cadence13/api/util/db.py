from flask_sqlalchemy import SQLAlchemy
from cadence13.db.tables import Base

db = SQLAlchemy(model_class=Base)
