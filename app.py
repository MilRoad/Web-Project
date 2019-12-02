import psycopg2
from flask import Flask, render_template, request,jsonify
import constant

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
        for i in request.form:
            print(i)
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        name_table = 'programmer' if len(request.form) == 6 else 'customer'
        print(1)
        cur.execute(
            f'insert into {name_table} (email, password, first_name, last_name, phone, stars) values (%s, %s,%s,%s,%s, %s)',
            (email, password, first_name, last_name, phone, 0))
        conn.commit()
        print(1)
    return jsonify({'data': 'ok'})


if __name__ == '__main__':
    app.run(debug=True)
