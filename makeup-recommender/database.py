from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserPreferences(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    skin_type = db.Column(db.String(50))
    undertone = db.Column(db.String(50))
    color_preferences = db.Column(db.String(200))
    budget_range = db.Column(db.String(50))

class FavoriteCelebrity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    image_url = db.Column(db.String(200))

class FavoriteProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.String, nullable=False) 
    name = db.Column(db.String, nullable=False)
    brand = db.Column(db.String)
    price = db.Column(db.Float)
    description = db.Column(db.String)
    image_url = db.Column(db.String)
    category = db.Column(db.String)