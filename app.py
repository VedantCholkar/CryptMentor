from flask import Flask, render_template, url_for, request as flask_request
import requests
from sqlalchemy import create_engine, Column, Integer, String, Float, inspect
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base

app = Flask(__name__)

engine = create_engine('sqlite:///database.db')
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False,bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

class Crypto(Base):
    __tablename__ = 'crypto'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True)
    price = Column(Float)
    quantity = Column(Float)
    money = Column(Float, default=100000.0)

    
    def __init__(self, name=None, price=None, quantity=None, money=None):
        self.name = name
        self.price = price
        self.quantity = quantity
        self.money = money
        
    def __repr__(self):
        return f'<Name {self.name} Price {self.price} Quantity {self.quantity} Money {self.money}>'    

inspector = inspect(engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def reset_db():
    if inspector.has_table('crypto'):
        Crypto.__table__.drop(engine)
    else:
        pass

with app.app_context():
    # reset_db()
    init_db()

if Crypto.query.filter(Crypto.name == 'money').first():
    pass
else:
    default = Crypto('money', 0.0, 0.0)
    db_session.add(default)
    db_session.commit()

def current_money():
    money_list = Crypto.query.filter(Crypto.name == 'money').first()
    money = money_list.money
    return money

def all():
    print(Crypto.query.all())

def add_coin(name, price, quantity):
    if Crypto.query.filter(Crypto.name == name).first():
        coin_list = Crypto.query.filter(Crypto.name == name).first()
        coin_list.quantity += quantity
        cost = price * quantity
        coin_list.price = price
        money_list = Crypto.query.filter(Crypto.name == 'money').first()
        money_list.money -= cost
        money_list.money = float("{:.2f}".format(money_list.money))
        db_session.commit()
    else:
        coin = Crypto(name, price, quantity)
        money_list = Crypto.query.filter(Crypto.name == 'money').first()
        money = money_list.money
        cost = price * quantity
        money_list.money -= cost
        db_session.add(coin)
        db_session.commit()

    return

def request(name):
    api_key = '2b1eb04a-e146-49ab-a881-96508aaaf573'

    parameters = {
        'CMC_PRO_API_KEY' : api_key,
        'slug' : name
    }

    response = requests.get("https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest", params=parameters)

    if response.status_code == 400:
        return 400
    else:
        response = response.json()
        first = next(iter(response['data'].items()))
        first_key, first_value = first
        price = first_value['quote']['USD']['price']

        return price



def buy_coin(name, quantity):
    price = request(name)
    if price == 400:
        return 'Bad request'
    if quantity <= 0:
        return 'Invalid quantity'
    price = float("{:.2f}".format(price))

    total_cost = price * quantity

    if total_cost > current_money():
        return 'Not enough money.'
    else:
        add_coin(name, price, quantity)
        return



def sell_coin(name, quantity):
    quantity = float(quantity)
    price = request(name)
    if price == 400:
        return 'Bad request'
    if quantity <= 0:
        return 'Invalid quantity'
    price = float("{:.2f}".format(price))

    if Crypto.query.filter(Crypto.name == name).first():
        q_list = Crypto.query.filter(Crypto.name == name).first()
        q_available = q_list.quantity
        if q_available >= quantity:
            q_list.quantity -= quantity
            money = quantity * price
            money_list = Crypto.query.filter(Crypto.name == 'money').first()
            money_list.money += money
            db_session.commit()
        else:
            print('Not enough coins.')
    else:
        print('Coins not owned.')

def valuation():
    c_list = Crypto.query.all()
    valuation = 0
    for i in c_list:
        quantity, price = i.quantity, i.price
        valuation += quantity * price
    return valuation


@app.route("/")
def homepage():
    money = current_money()
    val = valuation()
    total_valuation = money + float(val)
    money = "₹ {:,.2f}".format(money)
    pl = total_valuation - 100000.0
    c_list = Crypto.query.all()
    return render_template('index.html', money=money, valuation="₹ {:,.2f}".format(total_valuation), investment="₹ {:,.2f}".format(val), pl="₹ {:,.2f}".format(pl), c_list=c_list)

@app.route('/buy', methods=['POST', 'GET'])
def buy():
    if flask_request.method == 'POST':
        name = flask_request.form['c_name']
        quantity = float(flask_request.form['quantity'])
        buy_coin(name, quantity)
        return render_template("buy.html")
    else:
        return render_template("buy.html")
    
@app.route('/sell', methods=['POST', 'GET'])
def sell():
    if flask_request.method == 'POST':
        quantity = flask_request.form['quantity']
        name = flask_request.form['c_name']
        sell_coin(name, quantity)
        return render_template("sell.html")
    else:
        c_list = Crypto.query.all()
        return render_template("sell.html", c_list=c_list)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)