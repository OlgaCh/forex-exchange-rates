from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from config.settings import MYSQL_URI
from utils.grab_and_save import grab_and_save_rate, jsonify_data

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = MYSQL_URI

db = SQLAlchemy(app)
session = db.session


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
    return jsonify_data()

# GET request to show last N exchange operations
@app.route('/last/<int:n>', methods=['GET'])
@app.route('/last/<int:n>/', methods=['GET'])
def get_last_n(n):
    """
    Return last operation stored in MySQL and Redis
    """
    return jsonify_data(n=n)


# GET request to show last exchange operation for specific currency
@app.route('/last/<currency>', methods=['GET'])
@app.route('/last/<currency>/', methods=['GET'])
def get_last_currency(currency):
    """
    Return last operation stored in MySQL and Redis
    """
    return jsonify_data(currency=currency)


# GET request to show last N exchange operations for specific currency
@app.route('/last/<currency>/<int:n>', methods=['GET'])
@app.route('/last/<currency>/<int:n>/', methods=['GET'])
def get_last_n_currency(currency, n):
    """
    Return last operation stored in MySQL and Redis
    """
    return jsonify_data(n=n, currency=currency)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
