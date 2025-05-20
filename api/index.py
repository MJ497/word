# api/index.py

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# ─── Init Flask ────────────────────────────────────────────
app = Flask(__name__, template_folder="../templates", static_folder="../static")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '../site.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.environ.get("SECRET_KEY", "dev")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ─── Models ────────────────────────────────────────────────
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    def set_password(self, pw):   self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash,pw)

class LeaderboardEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    score       = db.Column(db.Integer, nullable=False)
    level       = db.Column(db.String(20), nullable=False)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

class Word(db.Model):
    id    = db.Column(db.Integer, primary_key=True)
    text  = db.Column(db.String(50), unique=True, nullable=False)
    level = db.Column(db.String(20), nullable=False)

# ─── Routes ───────────────────────────────────────────────
@app.before_first_request
def init_db():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/words')
def get_words():
    all_words = Word.query.all()
    out = {'easy':[], 'medium':[], 'hard':[]}
    for w in all_words:
        out[w.level].append(w.text.upper())
    return jsonify(out)

@app.route('/api/leaderboard', methods=['GET','POST'])
def leaderboard():
    if request.method=='GET':
        limit  = int(request.args.get('limit',10))
        offset = int(request.args.get('offset',0))
        entries = LeaderboardEntry.query\
                   .order_by(LeaderboardEntry.score.desc(), LeaderboardEntry.timestamp)\
                   .offset(offset).limit(limit)
        return jsonify([{
            'rank': i+offset+1,
            'player': e.player_name,
            'score':  e.score,
            'level':  e.level
        } for i,e in enumerate(entries)])
    # POST
    data = request.json
    e = LeaderboardEntry(
      player_name=data['player'],
      score=data['score'],
      level=data['level']
    )
    db.session.add(e)
    db.session.commit()
    return jsonify({'ok':True}),201

# … add your other Flask routes here (signup/login/dashboard/etc) …

if __name__ == "__main__":
    # for local debugging
    app.run(debug=True)
