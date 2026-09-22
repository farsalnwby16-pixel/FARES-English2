import os
from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Lesson(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    level = db.Column(db.String(10), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    youtube_url = db.Column(db.String(300), nullable=False)

# مسار عرض الشهادة
@app.route('/certificate')
def view_certificate():
    name = request.args.get('name', 'الطالب')
    date = datetime.now().strftime('%B %d, %Y')
    return render_template('certificate.html', name=name, date=date)

if __name__ == '__main__':
    app.run(debug=True)
