import redis
import logging

from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc

from config.settings import MYSQL_URI, REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PWD
from models.models import ExchangeRate
from utils.grab_and_save import grab_and_save_rate

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI

db = SQLAlchemy(app)
session = db.session

# setting up Redis connection
redis_db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                             password=REDIS_PWD, decode_responses=True)


# POST Request to get exchange rates
@app.route('/grab_and_save/<currency>/<amount>', methods=['POST', 'GET'])
@app.route('/grab_and_save/<currency>/<amount>/', methods=['POST', 'GET'])
def get_exchange_data(currency, amount):
    """
    Sending POST request to OXR API to get latest exchange rate for specified params.

    :param currency: str - 3-digit currency repr.
    :param amount: float - amount to change
    """
    grab_and_save_rate(currency=currency, original_amount=float(amount))
    return render_template('main.html', currency=currency, amount=amount)

# GET request to show last exchange operation
@app.route('/last', methods=['GET'])
@app.route('/last/', methods=['GET'])
def get_last():
    """
    Return last operation stored in MySQL and Redis
    """
    # MySQL
    last_ms = session.query(ExchangeRate).order_by(desc(ExchangeRate.timestamp)).first()
    # Redis
    keys = redis_db.keys()
    keys.sort(reverse=True)

    if not len(keys):
        logging.warning('Exchange rates were requested. No data in database.')
        return jsonify(APIWarning='There is no exchange rates in database')

    last_redis = redis_db.hgetall(keys[0])

    return jsonify(MySQL=last_ms.serialize, Redis=last_redis)

# GET request to show last N exchange operations
@app.route('/last/<int:n>', methods=['GET'])
@app.route('/last/<int:n>/', methods=['GET'])
def get_last_n(n):
    """
    Return last operation stored in MySQL and Redis
    """
    # MySQL
    last_ms = session.query(ExchangeRate).order_by(desc(ExchangeRate.timestamp)).limit(n)
    # Redis
    keys = redis_db.keys()
    keys.sort(reverse=True)

    exchange_count = len(keys)
    if exchange_count < n:
        logging.warning(f'Requested last {n} exchanges. Data only for {exchange_count} rates present')
        return jsonify(APIWarning=f'Too large number of exchange rates. Only '
                                  f'{exchange_count} rates present')

    return jsonify(MySQL=[ms.serialize for ms in last_ms],
                   Redis=[redis_db.hgetall(keys[i]) for i in range(n)])


# GET request to show last exchange operation for specific currency
@app.route('/last/<currency>', methods=['GET'])
@app.route('/last/<currency>/', methods=['GET'])
def get_last_currency(currency):
    """
    Return last operation stored in MySQL and Redis
    """
    # MySQL
    last_ms = session.query(ExchangeRate).filter(ExchangeRate.currency == currency)\
        .order_by(desc(ExchangeRate.timestamp)).first()
    # Redis
    keys = [k for k in redis_db.keys() if currency in k]
    keys.sort(reverse=True)

    if not len(keys):
        logging.warning(f'Exchange rates for {currency} were requested. No data in database.')
        return jsonify(APIWarning=f'There is no exchange rates for {currency} in database')

    last_redis = redis_db.hgetall(keys[0])

    return jsonify(MySQL=last_ms.serialize, Redis=last_redis)


# GET request to show last N exchange operations for specific currency
@app.route('/last/<currency>/<int:n>', methods=['GET'])
@app.route('/last/<currency>/<int:n>/', methods=['GET'])
def get_last_n_currency(currency, n):
    """
    Return last operation stored in MySQL and Redis
    """
    # MySQL
    last_ms = session.query(ExchangeRate).filter(ExchangeRate.currency == currency).\
        order_by(desc(ExchangeRate.timestamp)).limit(n)
    # Redis
    keys = [k for k in redis_db.keys() if currency in k]
    keys.sort(reverse=True)

    exchange_count = len(keys)
    if exchange_count < n:
        logging.warning(f'Requested last {n} exchanges for {currency}. Data only for {exchange_count}'
                        f' rates present')
        return jsonify(APIWarning=f'Too large number of exchange rates for {currency}. '
                                  f'Only {exchange_count} rates present')

    return jsonify(MySQL=[ms.serialize for ms in last_ms],
                   Redis=[redis_db.hgetall(keys[i]) for i in range(n)])


if __name__ == '__main__':
    app.run(host='0.0.0.0')
