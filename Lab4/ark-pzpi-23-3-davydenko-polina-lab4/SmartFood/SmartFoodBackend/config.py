from flask_sqlalchemy import SQLAlchemy
from flask import Flask
import os

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mssql+pyodbc://DESKTOP-5GUF215\\SQLEXPRESS/SmartFood?driver=ODBC+Driver+18+for+SQL+Server&Trusted_Connection=yes&Encrypt=no"
)

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "dev-secret")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JSON_AS_ASCII"] = False

db = SQLAlchemy(app)
