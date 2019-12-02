import psycopg2
from flask import Flask, render_template, request,jsonify
import constant
from werkzeug.security import generate_password_hash,  check_password_hash

app = Flask(__name__)


conn = psycopg2.connect(host=constant.host, dbname=constant.dbname, user=constant.username, password=constant.password)
cur = conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')

#
# @app.route('/db')
# def db():
#     cur.execute("select * from languages where name=%s", ('Python',))
#     metros_info = cur.fetchall()
#     json_response = {
#         'language': []
#     }
#     print(metros_info)
#     for i in metros_info:
#
#         json_response['language'].append(i)
#     return jsonify(json_response)


@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        print(password)
        phone = request.form['phone']
        name_table = 'programmer' if len(request.form) == 6 else 'customer'
        try:
            cur.execute(
                f'insert into {name_table} (email, password, first_name, last_name, phone, stars) values (%s, %s,%s,%s,%s, %s)',
                (email, password, first_name, last_name, phone, 0))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            return 'По данному email пользователь зарегистрирован'
    return jsonify({'data': 'ok'})

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        


if __name__ == '__main__':
    app.run(debug=True)
