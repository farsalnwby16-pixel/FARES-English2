from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return "الصفحة الرئيسية شغالة تمام! <a href='/certificate?name=فارس'>اضغط هنا لعرض الشهادة</a>"

@app.route('/certificate')
def view_certificate():
    name = request.args.get('name', 'الطالب')
    date = datetime.now().strftime('%B %d, %Y')
    return f"<h1>مبروك يا {name}!</h1><p>تاريخ الإصدار: {date}</p>"

if __name__ == '__main__':
    app.run(debug=True, port=5000)
