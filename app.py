import psycopg2
from flask import Flask, render_template, request, session, redirect, url_for
import constant
from werkzeug.security import generate_password_hash,  check_password_hash
import json
from flask_dance.contrib.github import make_github_blueprint, github

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisissupposedtobesecretkey'
conn = psycopg2.connect(host=constant.host, dbname=constant.dbname, user=constant.username, password=constant.password)
cur = conn.cursor()

github_blueprint = make_github_blueprint(client_id='7cb78323c53d79e6775e', client_secret='996e19b937a943f053cfddcfcd5977a9d2d604fa')

app.register_blueprint(github_blueprint, url_prefix='/github_login')


@app.route('/github')
def github_login():
    if not github.authorized:
        return redirect(url_for('github.login'))
    account_info = github.get('/user')
    if account_info.ok:
        account_info_json = account_info.json()
        email = account_info_json['login']
        session['email'] = email
        session['type'] = 'programmer'
        cur.execute('select * from emails where email=%s', (email,))
        user = cur.fetchone()
        if user == None:
            status = 'False'
            cur.execute('insert into emails (email, status) values (%s, %s) returning id', (email, status))
            conn.commit()
            return render_template('github.html', email=email)
        else:
            if user[2] == 'False':
                return render_template('github.html', email=email)
            else:
                id = user[0]
                return redirect(f'/profile/{id}')
    return '<h1> Request failed </h1>'


@app.route('/add_github')
def add_github():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    phone = request.form['phone']
    email = session['email']

    cur.execute('insert into programmer (email, password, first_name, last_name, phone, stars, status) values (%s, %s,%s,%s,%s, %s, %s)',
                (email, 'github', first_name, last_name, phone, 0, False))
    conn.commit()

    cur.execute('update emails set status=%s where email=%s',
        ('programmer',email))
    conn.commit()

    return redirect('/interests')



@app.route('/')
def index():
    return render_template('index.html')


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
            stars = ', stars, status'
            count = (email, password, first_name, last_name, phone, 0,False)
            position = ', %s, %s'
            cur.execute('select email from customer where email=%s',(email,))
            if cur.fetchall() != []:
                return 'Вы являетесь работодателем и не можете зарегистрироваться, как программист'
        else:
            name_table = 'customer'
            stars = ''
            count = (email, password, first_name, last_name, phone)
            position = ''
            cur.execute('select email from programmer where email=%s', (email,))
            if cur.fetchall() != []:
                return 'Вы являетесь программистом и не можете зарегистрироваться, как разработчик'

        try:
            cur.execute(
                f'insert into {name_table} (email, password, first_name, last_name, phone{stars}) values (%s, %s,%s,%s,%s{position})',
                count)
            cur.execute('insert into emails (email, status) values (%s, %s) returning id', (email, name_table))
            person_id = cur.fetchone()[0]
            conn.commit()
            session['email'] = email
            session['type'] = name_table
        except psycopg2.errors.UniqueViolation:
            conn.commit()
            return render_template('error_registr.html')
    if name_table == 'programmer':
        return redirect('/description')
    return redirect(f'/profile/{person_id}')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur.execute('select email, password from admin where email=%s', (email,))
        admin = cur.fetchone()
        print(admin)
        if admin != None:
            adm_pass = admin[1]
            if adm_pass == password:
                return redirect('/profile_admin')
            else:
                return render_template('error_login.html')

        else:

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
            conn.commit()
            cur.execute('select id from emails where email=%s', (session['email'],))
            id = cur.fetchone()[0]
        return redirect(f'/profile/{id}')


@app.route('/logout')
def logout():
       # remove the username from the session if it is there
       session.pop('email', None)
       return render_template('index.html')



@app.route('/description')
def description():
    cur.execute('select * from languages')
    languages = cur.fetchall()
    cur.execute('select * from areas')
    areas = cur.fetchall()
    conn.commit()
    all_lang = []
    all_areas = []

    for lang in languages:
        lang_info = {
            'id': lang[1],
            'name': lang[0],
        }
        all_lang.append(lang_info)

    for area in areas:
        area_info = {
            'name': area[1],
            'id': area[0],
        }
        all_areas.append(area_info)

    return render_template('prog_information.html', languages=all_lang, areas=all_areas)



@app.route('/interests', methods=['POST'])
def interests():
    languages = request.form.getlist('lang')
    areas = request.form.getlist('area')
    description = request.form['description']
    email = session['email']

    for i in areas:
        cur.execute('select * from areas where id=%s', (i,))
        area = cur.fetchone()
        if area != []:
            cur.execute('select * from programmer_areas where areas_id=%s and programmer_email=%s', (i,email,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into programmer_areas (programmer_email, areas_id) values (%s, %s)',
                    (email, i))

    for i in languages:
        cur.execute('select * from languages where id=%s', (i,))
        lang = cur.fetchone()
        if lang != []:
            cur.execute('select * from programmer_languages where languages_id=%s and programmer_email=%s', (i, email,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into programmer_languages (programmer_email, languages_id) values (%s, %s)',
                    (email, i))

    cur.execute(
        'update programmer set description=%s where email=%s',
        (description,email))

    conn.commit()
    cur.execute('select id from emails where email=%s',(session['email'],))
    id = cur.fetchone()[0]
    return redirect(f'/profile/{id}')

@app.route('/profile')
def profile():
    email = session['email']
    admin = True
    if session['type'] == 'programmer':
        sql1 = """
        SELECT name FROM areas
        WHERE id IN
            (SELECT areas_id 
             FROM programmer_areas
             WHERE programmer_email=%s)"""
        sql2 = """
                SELECT name FROM languages
                WHERE id IN
                    (SELECT languages_id 
                    FROM programmer_languages
                    WHERE programmer_email=%s)"""
        sql3 = """
        SELECT first_name, last_name, description, status FROM programmer WHERE email=%s"""
        cur.execute(sql1, (email,))
        areas = cur.fetchall()
        cur.execute(sql2, (email,))
        langs = cur.fetchall()
        cur.execute(sql3, (email,))
        person = cur.fetchone()
        conn.commit()

        all_lang = []
        all_areas = []

        for i in areas:
            all_areas.append(i[0])
        for i in langs:
            all_lang.append(i[0])
        name = person[0] + " " + person[1]
        description = person[2]
        prog_status = person[3]

        session['languages'] = all_lang
        session['areas'] = all_areas

        return render_template('profile.html', languages=all_lang, areas=all_areas, name=name, description=description, status=session['type'], admin=admin, prog_status = prog_status)
    else:
        sql4 = """
                SELECT first_name, last_name FROM customer WHERE email=%s"""
        cur.execute(sql4, (email,))
        person = cur.fetchone()
        conn.commit()
        name = person[0] + " " + person[1]

        cur.execute('select * from orders where customer_email=%s',(email,))
        orders = cur.fetchall()
        ord_wait = []
        ord_progress = []
        ord_done = []
        print(orders)
        for i in orders:
            print(i)
            cur.execute('select status from programmers_orders where orders_id=%s', (i[0],))
            status = cur.fetchall()

            if status == []:
                ord_info = {
                    'id': i[0],
                    'description': i[1],
                    'status': i[2]
                }
                ord_wait.append(ord_info)
            else:
                k = 0
                for j in status:
                    if j[0] == 1 and k == 0:
                        ord_info = {
                            'id': i[0],
                            'description': i[1],
                            'status': i[2]
                        }
                        ord_wait.append(ord_info)
                        k += 1
                    if j[0] == 2:
                        ord_info = {
                            'id': i[0],
                            'description': i[1],
                        }
                        ord_progress.append(ord_info)
                    if j[0] == 3:
                        ord_info = {
                            'id': i[0],
                            'description': i[1],
                        }
                        ord_done.append(ord_info)
        return render_template('profile.html', name=name, status=session['type'], orders_wait=ord_wait, orders_progress=ord_progress, orders_done=ord_done, admin=admin)


@app.route('/create_orders', methods=['GET'])
def orders():
    cur.execute('select * from languages')
    languages = cur.fetchall()
    cur.execute('select * from areas')
    areas = cur.fetchall()
    conn.commit()
    all_lang = []
    all_areas = []

    for lang in languages:
        lang_info = {
            'id': lang[1],
            'name': lang[0],
        }
        all_lang.append(lang_info)

    for area in areas:
        area_info = {
            'name': area[1],
            'id': area[0],
        }
        all_areas.append(area_info)

    return render_template('create_orders.html', languages=all_lang, areas=all_areas)

@app.route('/add_orders', methods=['POST'])
def add_orders():
    email = session['email']

    cur.execute('select id from emails where email=%s', (email,))
    cust_id = cur.fetchone()[0]

    languages = request.form.getlist('lang')
    areas = request.form.getlist('area')
    description = request.form['description']

    cur.execute('insert into orders (description, customer_email, status) values (%s, %s, %s) returning id ', (description, email, False))
    order_id = cur.fetchone()[0]

    for i in areas:
        cur.execute('select * from areas where id=%s', (i,))
        area = cur.fetchone()
        if area != []:
            cur.execute('select * from orders_areas where areas_id=%s and orders_id=%s', (i, order_id,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into orders_areas (orders_id, areas_id) values (%s, %s)',
                    (order_id, i))


    for i in languages:
        cur.execute('select * from languages where id=%s', (i,))
        lang = cur.fetchone()
        if lang != []:
            cur.execute('select * from orders_languages where languages_id=%s and orders_id=%s', (i, order_id,))
            if cur.fetchall() == []:
                cur.execute(
                    'insert into orders_languages (orders_id, languages_id) values (%s, %s)',
                    (order_id, i))
    conn.commit()
    return redirect(f'/profile/{cust_id}')

@app.route('/find_order', methods=['GET'])
def find_order():
    type = session['type']
    if type == 'programmer':
        all_lang = session['languages']
        all_areas = session['areas']

        orders_id = []
        for i in all_lang:
            sql = """
            SELECT orders_id FROM orders_languages
            WHERE languages_id IN
            (SELECT id 
             FROM languages
             WHERE name=%s)"""
            cur.execute(sql, (i,))
            ord = cur.fetchall()
            conn.commit()
            for j in ord:
                if j not in orders_id:
                    orders_id.append(j)

        for i in all_areas:
            sql = """
            SELECT orders_id FROM orders_areas
            WHERE areas_id IN
            (SELECT id 
             FROM areas
             WHERE name=%s)"""
            cur.execute(sql, (i,))
            ord = cur.fetchall()
            conn.commit()
            for j in ord:
                if j not in orders_id:
                    orders_id.append(j)
        all_orders = []
        for i in orders_id:
            cur.execute('select * from orders where id = %s ', (i,))
            order = cur.fetchone()
            cur.execute('select status from programmers_orders where orders_id = %s ', (order[0],))
            status = cur.fetchall()
            order_stat = 0
            for j in status:
                if j[0] == 3:
                    order_stat = 1
            if order_stat == 0:
                order_info = {
                    'id': order[0],
                    'description': order[1],
                    'customer_name': order[2],
                    'status': order[3]
                }
                all_orders.append(order_info)
                conn.commit()

        return render_template("tasks.html", orders=all_orders)
    else:
        return render_template("tasks.html")

@app.route('/order_info/<int:order_id>', methods=['GET'])
def order_info(order_id):
    cur.execute('select * from orders where id = %s', (order_id,))
    order = cur.fetchone()
    conn.commit()
    description = order[1]
    customer_email = order[2]

    cur.execute('select first_name, last_name, phone from customer where email = %s', (customer_email,))
    customer = cur.fetchone()
    customer_name = customer[0] + " " + customer[1]
    cust_phone = '+7' + customer[2]

    cur.execute('select id from emails where email = %s', (customer_email,))
    customer_id = cur.fetchone()[0]

    cur.execute('select id from emails where email = %s', (session['email'],))
    user_id = cur.fetchone()[0]

    sql1 = """
            SELECT name FROM areas
            WHERE id IN
                (SELECT areas_id 
                 FROM orders_areas
                 WHERE orders_id=%s)"""
    sql2 = """
                    SELECT name FROM languages
                    WHERE id IN
                        (SELECT languages_id 
                        FROM orders_languages
                        WHERE orders_id=%s)"""

    cur.execute(sql2, (order_id,))
    languages = cur.fetchall()
    cur.execute(sql1, (order_id,))
    areas = cur.fetchall()
    conn.commit()


    cur.execute('select programmer_email, status from programmers_orders where orders_id=%s', (order_id,))
    prog_order = cur.fetchall()
    programmers = []
    k = 0
    for i in prog_order:
        cur.execute('select first_name, last_name, phone from programmer where email=%s', (i[0],))
        name = cur.fetchone()
        cur.execute('select id from emails where email=%s', (i[0],))
        id = cur.fetchone()[0]
        conn.commit()
        prog_info = {
            'email': i[0],
            'status': i[1],
            'name': name[0] + ' ' + name[1],
            'id': id,
            'phone': '+7' + name[2]
        }
        if i[1] == 3:
            k = 3
        if i[1] == 2:
            k = 2
        programmers.append(prog_info)


    if k == 0:
        order_status = 1 #не завершен
    elif k == 3:
        order_status = 3 #завершен
    else:
        order_status = 2 #в разработке
    order_info = {
        'id': order_id,
        'description': description,
        'customer_email': customer_email,
        'customer_name': customer_name,
        'languages': [i[0] for i in languages],
        'areas': [i[0] for i in areas],
        'programmers': programmers,
        'customer_id': customer_id,
        'user_id': user_id,
        'status': order_status,
        'cust_phone': cust_phone
    }
    with open('db.json','w') as file:
        json.dump(order_info, file)
    return render_template('orders.html', orders=order_info, status=session['type'])

# status 1 - программист хочет взять заказ, но не одобрен еще заказчиком
# status 0 - программист хотел взять заказ, но заказчик отказался
# status 2 - программист получил заказ, он в процессе работы
# status 3 - программист выполнил заказ
@app.route('/take_order/<int:order_id>', methods=['POST', 'GET'])
def take_order(order_id):
    email = session['email']
    cur.execute('select * from programmers_orders where programmer_email=%s and orders_id=%s', (email,order_id,))
    person = cur.fetchone()
    print(person)
    if person == None:
        cur.execute('insert into programmers_orders (programmer_email, orders_id, status) values (%s,%s,%s)', (email, order_id, 1))
        conn.commit()
    return render_template('success.html')

@app.route('/profile/<int:id>', methods=['GET'])
def profile_view(id):
    cur.execute('select email, status from emails where id=%s',(id,))
    person = cur.fetchone()
    email = person[0]
    status = person[1]

    if session['email'] == email:
        admin = True
    else:
        admin = False

    if status == 'programmer':
        sql1 = """
                SELECT name FROM areas
                WHERE id IN
                    (SELECT areas_id 
                     FROM programmer_areas
                     WHERE programmer_email=%s)"""
        sql2 = """
                        SELECT name FROM languages
                        WHERE id IN
                            (SELECT languages_id 
                            FROM programmer_languages
                            WHERE programmer_email=%s)"""
        sql3 = """
                SELECT first_name, last_name, description, stars, status FROM programmer WHERE email=%s"""
        cur.execute(sql1, (email,))
        areas = cur.fetchall()
        cur.execute(sql2, (email,))
        langs = cur.fetchall()
        cur.execute(sql3, (email,))
        person = cur.fetchone()
        conn.commit()

        all_lang = []
        all_areas = []

        for i in areas:
            all_areas.append(i[0])
        for i in langs:
            all_lang.append(i[0])
        name = person[0] + " " + person[1]
        description = person[2]
        stars = person[3]
        prog_status = person[4]
        star = []
        for i in range(5):
            if stars >= 1:
                star.append(2)
            elif stars >=0.5:
                star.append(1)
            else:
                star.append(0)
            stars -= 1

        session['languages'] = all_lang
        session['areas'] = all_areas

        cur.execute('select orders_id, status from programmers_orders where programmer_email=%s', (email,))
        orders = cur.fetchall()
        ord_wait = []
        ord_progress = []
        ord_done = []
        for i in orders:
            cur.execute('select description, status from orders where id=%s', (i[0],))
            ord = cur.fetchone()
            if i[1] == 1:
                ord_info = {
                    'id': i[0],
                    'description': ord[0],
                    'status': ord[1]
                }
                ord_wait.append(ord_info)
            if i[1] == 2:
                ord_info = {
                    'id': i[0],
                    'description': ord[0],
                }
                ord_progress.append(ord_info)
            if i[1] == 3:
                ord_info = {
                    'id': i[0],
                    'description': ord[0],
                }
                ord_done.append(ord_info)



        return render_template('profile.html', languages=all_lang, areas=all_areas, name=name, description=description,
                               status=status, admin=admin, stars=star, orders_wait=ord_wait,
                               orders_progress=ord_progress, orders_done=ord_done, prog_stat=prog_status)
    else:
        sql4 = """
                        SELECT first_name, last_name FROM customer WHERE email=%s"""
        cur.execute(sql4, (email,))
        person = cur.fetchone()
        conn.commit()
        name = person[0] + " " + person[1]

        cur.execute('select * from orders where customer_email=%s', (email,))
        orders = cur.fetchall()
        ord_wait = []
        ord_progress = []
        ord_done = []

        for i in orders:
            cur.execute('select status from programmers_orders where orders_id=%s', (i[0],))
            status = cur.fetchall()
            print(i[3])
            if status == []:
                ord_info = {
                    'id': i[0],
                    'description': i[1],
                    'status': i[3]
                }
                ord_wait.append(ord_info)
            else:
                k, l, m = 0, 0, 0
                for j in status:
                    if j[0] == 1 and k == 0:
                        ord_info = {
                            'id': i[0],
                            'description': i[1],
                            'status': i[3]
                        }
                        ord_wait.append(ord_info)
                        k += 1
                    if j[0] == 2 and l == 0:
                        ord_info = {
                            'id': i[0],
                            'description': i[1],
                        }
                        ord_progress.append(ord_info)
                        l +=1
                    if j[0] == 3 and m == 0:
                        ord_info = {
                            'id': i[0],
                            'description': i[1],
                        }
                        ord_done.append(ord_info)
                        m += 0
            print(ord_wait)
        return render_template('profile.html', name=name, status=session['type'], orders_wait=ord_wait,
                               orders_progress=ord_progress, orders_done=ord_done, admin=admin)


@app.route('/start_order/<int:order_id>/<email>', methods=['GET'])
def start_order(order_id, email):
    cur.execute('update programmers_orders set status=%s where programmer_email=%s and orders_id=%s  and status=%s',(2,email, order_id, 1))
    conn.commit()
    return redirect(f'/order_info/{order_id}')

@app.route('/stars_order/<int:order_id>', methods=['GET'])
def stars_order(order_id):
    cur.execute('select programmer_email from programmers_orders where status=%s and orders_id=%s', (3, order_id))
    programmer = cur.fetchall()
    all_programmer = []
    for i in programmer:
        cur.execute('select first_name, last_name from programmer where email=%s',(i[0],))
        info = cur.fetchone()
        people_info={
            'name': info[0] + ' ' + info[1],
            'email': i[0]
        }
        all_programmer.append(people_info)
    return render_template('finish_order.html', programmers=all_programmer,order_id=order_id)

@app.route('/finish_order/<int:order_id>', methods=['GET'])
def finish_order(order_id):
    cur.execute('update programmers_orders set status=%s where orders_id=%s and status=%s',(3, order_id, 2))
    cur.execute('update programmers_orders set status=%s where orders_id=%s and status=%s', (0, order_id, 1))
    conn.commit()

    return redirect(f'/stars_order/{order_id}')


@app.route('/stars_programmer/<int:order_id>', methods=['POST'])
def stars_programmer(order_id):

    email_user = []
    for i in request.form:
        email_user.append(i)
    for i in email_user:

        cur.execute('select count(id) from programmers_orders where programmer_email=%s and status=%s',(i,3))
        count = cur.fetchone()[0]
        cur.execute('select stars from programmer where email=%s',(i,))
        stars = cur.fetchone()[0]
        stars = (stars * (count-1) + int(request.form[i]))/count
        cur.execute('update programmer set stars=%s where email=%s',(stars,i))
        conn.commit()



    return redirect(f'/order_info/{order_id}')

@app.route('/add_info', methods=['POST'])
def add_info():
    languages = request.form['lang'].split(',')
    areas = request.form['area'].split(',')

    print(languages, areas)

    for i in areas:
        cur.execute('select * from areas where name=%s', (i,))
        area = cur.fetchone()
        if area == None:
            cur.execute('insert into areas(name) values (%s)', (i,))

    for i in languages:
        cur.execute('select * from languages where name=%s', (i,))
        lang = cur.fetchone()
        if lang == None:
            cur.execute('insert into languages(name) values (%s)', (i,))

    conn.commit()
    return render_template('success_add.html')

@app.route('/profile_admin', methods=['GET'])
def profile_admin():
    cur.execute('select email, description from programmer where status=%s',(False,))
    programmers = cur.fetchall()
    progs = []

    for programmer in programmers:
        prog_info = {
            'email': programmer[0],
            'description': programmer[1]
        }
        progs.append(prog_info)

    cur.execute('select id, description from orders where status=%s', (False,))
    orders = cur.fetchall()
    ords = []

    for order in orders:
        ord_info = {
            'id': order[0],
            'description': order[1]
        }
        ords.append(ord_info)

    return render_template('profile_admin.html', programmers=progs, orders=ords)

@app.route('/confirm_order/<int:order_id>', methods=['GET'])
def confirm_order(order_id):
    cur.execute('update orders set status=%s where id=%s',(True, order_id,))
    conn.commit()

    return redirect('/profile_admin')


@app.route('/decline_order/<int:order_id>', methods=['GET'])
def decline_order(order_id):
    cur.execute('delete from orders where id=%s', (order_id,))
    conn.commit()

    return redirect('/profile_admin')


@app.route('/confirm_prog/<email>', methods=['GET'])
def confirm_prog(email):
    cur.execute('update programmer set status=%s where email=%s', (True, email,))
    conn.commit()

    return redirect('/profile_admin')

@app.route('/decline_prog/<email>', methods=['GET'])
def decline_prog(email):
    cur.execute('delete from programmer where email=%s', (email,))
    conn.commit()

    return redirect('/profile_admin')



if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.run(debug=True)
