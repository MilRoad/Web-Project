import psycopg2
from flask import Flask, render_template, request, jsonify, session,redirect
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
        if len(request.form) == 6:
            name_table = 'programmer'

            cur.execute('select email from customer where email=%s',(email,))
            if cur.fetchall() != []:
                return 'Вы являетесь работодателем и не можете зарегистрироваться, как программист'
        else:
            name_table = 'customer'
            cur.execute('select email from programmer where email=%s', (email,))
            if cur.fetchall() != []:
                return 'Вы являетесь программистом и не можете зарегистрироваться, как разработчик'

        try:
            cur.execute(
                f'insert into {name_table} (email, password, first_name, last_name, phone, stars) values (%s, %s,%s,%s,%s, %s)',
                (email, password, first_name, last_name, phone, 0))
            conn.commit()
            # session['email'] = email
        except psycopg2.errors.UniqueViolation:
            conn.commit()
            return render_template('error_registr.html')

    return redirect('/description')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur.execute('select email,password from programmer where email = (%s)', (email,))
        programmer = cur.fetchall()
        cur.execute('select email,password from customer where email = (%s)', (email,))
        customer = cur.fetchall()
        if programmer == [] and customer == []:
            return render_template('error_login.html')
        elif customer == []:
            if not (check_password_hash(programmer[0][1], password)):
                return render_template('error_login.html')
            session['email'] = email
            session['type'] = 'programmer'
        else:
            if not (check_password_hash(customer[0][1], password)):
                return render_template('error_login.html')
            session['email'] = email
            session['type'] = 'customer'
    return jsonify({'data': session['email']})

@app.route('/logout')
def logout():
       # remove the username from the session if it is there
       session.pop('email', None)
       return render_template('index.html')



@app.route('/test')
def test():
    if session['type'] == 'programmer':
        cur.execute('select description from programmer where email=%s',(session['email'],))
        if cur.fetchall()[0] == ():
            return redirect('/description')
    return render_template('profile.html')


@app.route('/description')
def test_descr():
    return render_template('prog_information.html')



@app.route('/ttt',methods=['POST'])
def ttt():
    print(request.form.getlist('lang'))
    print(request.form.getlist('area'))

    print(request.form['description'])

    return 'ok'



if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)
