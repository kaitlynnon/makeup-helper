from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import db, UserPreferences, FavoriteCelebrity, FavoriteProduct
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'dev-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///makeup.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)
with app.app_context():
    db.create_all()

CELEBRITIES = [
    {"id": 1, "name": "Jennie", "image": "jennie.jpg"},
    {"id": 2, "name": "IU", "image": "iu.jpg"},
    {"id": 3, "name": "Karina", "image": "karina.jpg"},
    {"id": 4, "name": "Wonyoung", "image": "wonyoung.jpg"},
    {"id": 5, "name": "Ariana Grande", "image": "arianagrande.jpg"},
    {"id": 6, "name": "Rose", "image": "rose.jpg"},
    {"id": 7, "name": "Ningning", "image": "ningning.jpg"},
]

def load_products():
    with open('static/data/generated_products.json') as f:
        return json.load(f)

def smart_product_recommender(skin_type, undertone, color_preferences, budget_range):
    all_products = load_products()
    filtered = []
    for product in all_products:
        match = 0
        if skin_type and skin_type.lower() in product["tags"]:
            match += 1
        if undertone and undertone.lower() in product["tags"]:
            match += 1
        if color_preferences and any(color.lower() in product["tags"] for color in color_preferences):
            match += 1
        price = float(product["price"])
        if (budget_range == "low" and price <= 20) or \
           (budget_range == "medium" and 20 < price <= 40) or \
           (budget_range == "high" and price > 40):
            match += 1
        if match >= 2:
            filtered.append(product)
    return filtered[:12]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        session['skin_type'] = request.form.get('skin_type')
        session['undertone'] = request.form.get('undertone')
        session['color_preferences'] = request.form.getlist('color_preferences')
        session['budget_range'] = request.form.get('budget_range')

        preferences = UserPreferences(
            skin_type=session['skin_type'],
            undertone=session['undertone'],
            color_preferences=",".join(session['color_preferences']),
            budget_range=session['budget_range']
        )
        db.session.add(preferences)
        db.session.commit()

        return redirect(url_for('select_celebrities'))
    return render_template('quiz.html')

@app.route('/celebrities', methods=['GET', 'POST'])
def select_celebrities():
    if request.method == 'POST':
        selected_celebrities = request.form.getlist('celebrities')
        session['selected_celebrities'] = selected_celebrities

        for celeb_id in selected_celebrities:
            celeb = next((c for c in CELEBRITIES if str(c['id']) == celeb_id), None)
            if celeb:
                favorite = FavoriteCelebrity(name=celeb['name'], image_url=celeb['image'])
                db.session.add(favorite)
        db.session.commit()

        return redirect(url_for('recommendations'))
    return render_template('celebrities.html', celebrities=CELEBRITIES)

CELEB_INSPO = [
    {
        "name": "Wonyoung",
        "image": "wonyoung.jpg",
        "style": "Youthful, pink-toned makeup with glowy skin and glitter lids.",
        "tags": ["pink", "glitter", "dewy", "youthful"]
    },
    {
        "name": "Karina",
        "image": "karina.jpg",
        "style": "Sleek cat eyes, gradient lips, and high-shine glass skin.",
        "tags": ["cat eyes", "gradient lips", "glass skin", "sleek"]
    },
    {
        "name": "Ningning",
        "image": "ningning.jpg",
        "style": "Bold eyeshadow, glossy lips, and high-contrast cheek highlight.",
        "tags": ["bold", "eyeshadow", "glossy", "highlight"]
    },
    {
        "name": "Ariana Grande",
        "image": "arianagrande.jpg",
        "style": "Signature winged eyeliner, nude lips, and lifted brows.",
        "tags": ["winged eyeliner", "nude lips", "brows"]
    },
    {
        "name": "IU",
        "image": "iu.jpg",
        "style": "Soft blush, sheer lips, and romantic peachy tones.",
        "tags": ["peachy", "blush", "romantic", "sheer"]
    },
    {
        "name": "Rosé",
        "image": "rose.jpg",
        "style": "Muted rose lips, light shimmer eyes, and cool-toned elegance.",
        "tags": ["shimmer", "rose", "cool-toned", "elegant"]
    },
    {
        "name": "Jennie",
        "image": "jennie.jpg",
        "style": "Chic cat eyes, matte lips, and subtle contour.",
        "tags": ["matte", "cat eyes", "chic", "contour"]
    }
]

@app.route("/celebrity-inspo")
def celebrity_inspo():
    return render_template("celebrity_inspo.html", celebs=CELEB_INSPO)

@app.route("/celeb-products/<celeb_name>")
def celeb_products(celeb_name):
    celeb = next((c for c in CELEB_INSPO if c["name"].lower() == celeb_name.lower()), None)
    if not celeb:
        return "Celebrity not found", 404

    all_products = load_products()
    recommendations = [
        p for p in all_products if any(tag in p.get("tags", []) for tag in celeb.get("tags", []))
    ]

    return render_template("celeb_products.html", celeb=celeb, recommendations=recommendations)

@app.route('/recommendations')
def recommendations():
    skin = session.get('skin_type')
    tone = session.get('undertone')
    colors = session.get('color_preferences', [])
    budget = session.get('budget_range')
    products = smart_product_recommender(skin, tone, colors, budget)
    return render_template('results.html', recommendations=products)

@app.route('/favorites')
def favorites():
    favorites = FavoriteProduct.query.all()
    return render_template('favorites.html', favorites=favorites)

@app.route('/remove-favorite/<int:product_id>', methods=['POST'])
def remove_favorite(product_id):
    product = FavoriteProduct.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('favorites'))

from flask import request, jsonify

@app.route('/add-favorite', methods=['POST'])
def add_favorite():
    data = request.get_json()

    if not data or 'product_id' not in data:
        return jsonify({'status': 'error', 'message': 'Invalid data'}), 400

    existing = FavoriteProduct.query.filter_by(product_id=data['product_id']).first()
    if existing:
        return jsonify({'status': 'exists', 'message': 'Already in favorites.'})

    new_favorite = FavoriteProduct(
        product_id=data['product_id'],
        name=data['product_name'],
        brand=data['product_brand'],
        price=float(data['product_price']),
        description=data['product_description'],
        image_url=data['product_image'],
        category=data['product_category']
    )
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Added to favorites!'})

with app.app_context():
    db.drop_all()
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, port=5001)