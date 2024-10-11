
from importlib.metadata import metadata
from flask import Flask, redirect, render_template, request, session
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, ForeignKey, Integer, Table, text
from sqlalchemy.orm import DeclarativeBase
app = Flask(__name__, static_url_path='/static')
app.debug = True

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

events_users = db.Table(
    'events_users',
    db.Column('nik_user', db.String(20)),
    db.Column('events_id', db.Integer, ForeignKey('events.id', name="fk_event_users_id"), primary_key=False),
    db.Column('users_id', db.Integer, ForeignKey('users.id', name="fk_event_users_id"),primary_key=False)
)

class Events(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    event_date = db.Column(db.String(50), unique=False, nullable=False)
    event_name = db.Column(db.String(100), unique=False, nullable=False)
    status_event = db.Column(db.Boolean, unique=False, nullable=True)
    max_redem = db.Column(db.Integer, unique=False, nullable=True)
    users = db.relationship('Users', secondary=events_users, backref=db.backref('event_assigned_users', lazy=True))

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    user_password = db.Column(db.String(50), unique=True, nullable=False)
    full_name = db.Column(db.String(100), unique=False, nullable=False)
    address = db.Column(db.String(500), unique=False, nullable=False)
    phone_number = db.Column(db.String(30), unique=False, nullable=False)
    is_active = db.Column(db.Boolean, unique=False, nullable=False)
    events = db.relationship('Events', secondary=events_users, backref=db.backref('user_applied_events', lazy=True))
    
@app.route('/')
def home():
    events = db.session.query(Events.id, Events.event_date, Events.event_name, Events.status_event, Events.max_redem).all()
    return render_template('index.html', events=events)

@app.route('/list-users')
def list_users():
    list_users = db.session.query(Users.id, Users.full_name, Users.address, Users.phone_number, Users.is_active).all() 
    return render_template('list-users.html', list_users=list_users)

@app.route('/add-user', methods=['POST'])
def add_users():
    user_name = request.form.get('user_name')
    password = request.form.get('password')
    activate_deactive = request.form.get('activate_deactive')
    full_name = request.form.get('full_name')
    address = request.form.get('address_user')
    phone_number = request.form.get('phone_number')
    if user_name != '' and password != '' and activate_deactive !='' and full_name!='' and address!='' and phone_number!='' :
        activate_deactive = eval(activate_deactive)
        user = Users(user_name = user_name, 
                     user_password = password, 
                     is_active = activate_deactive,
                     full_name = full_name,
                     address=address,
                     phone_number=phone_number)
        db.session.add(user)
        db.session.commit()
        return redirect('/list-users')
    else:
       return render_template('list-users.html')

@app.route('/add-event', methods=["POST"])
def add_event():
    event_date = request.form.get('event_date')
    event_name = request.form.get('event_name')
    activate_deactive = request.form.get('activate_deactive')
    event_max_redem = request.form.get('event_max_redem')
    try:
        event_max_redem = int(event_max_redem)
    except:
        event_max_redem = 0
    if event_date != '' and event_name != '' and activate_deactive !='' and event_max_redem !='':
        activate_deactive = eval(activate_deactive)
        event_model = Events(event_date = event_date, event_name = event_name, status_event = activate_deactive, max_redem=event_max_redem)
        db.session.add(event_model)
        db.session.commit()
        return redirect("/")
    else:
        return redirect("/")

@app.route('/list-event')
def list_event():
    return render_template('list-event.html')

@app.route('/redem-member-kyc')
def redem_member_kyc():
    sql = text('select events.id, events.event_name, events.event_date, users.full_name, events.max_redem ,count(events_users.nik_user) as "Redem Count" from events inner join events_users on(events.id=events_users.users_id) inner join users on(users.id=events_users.users_id) group by events_users.nik_user;')
    list_row = []
    with db.engine.connect() as connection:
        result = connection.execute(sql)
        for row in result:
            list_row.append(row)
    
    users = Users.query.all()
    events = Events.query.all()
    
    return render_template('redem-member-kyc.html', users = users, events = events, list_row = list_row)

@app.route('/add-redem', methods=["POST"])
def add_redem_user():
    user_id = request.form.get('user_id')
    event_id = request.form.get('event_id')
    nik_user = request.form.get('nik_user')
    sql = text('select events.id, events.event_name, events.event_date, users.full_name, events.max_redem ,count(events_users.nik_user) as "Redem Count" from events inner join events_users on(events.id=events_users.users_id) inner join users on(users.id=events_users.users_id) where events_users.events_id='+event_id+' and events_users.users_id='+user_id+' group by events_users.nik_user;')
    list_row = []
    with db.engine.connect() as connection:
        result = connection.execute(sql)
        for row in result:
            list_row.append(row)

    if user_id != '' and event_id != '' and nik_user !='' and list_row[0][5]<list_row[0][4]:
        new_event_user = events_users.insert().values(
            events_id = event_id,
            users_id = user_id,
            nik_user = nik_user
        )
        db.session.execute(new_event_user)
        db.session.commit()
        return "Success for redeem from this event"
    else:
        return "User has limit redeem for this event"
    

if __name__ == "__main__":
    app.run()