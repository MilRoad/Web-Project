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


@app.route('/register/', methods=['post', 'get'])
def register():
    if request.method == 'POST':
        print(request.form)
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        password = request.form.get('password')


if __name__ == '__main__':
    app.run(debug=True)
