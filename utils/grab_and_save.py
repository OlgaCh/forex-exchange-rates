import requests
import logging
import redis
from time import time

from flask import jsonify

from sqlalchemy import create_engine
from sqlalchemy import desc
from sqlalchemy.orm import Session

from config.settings import OXR_APIKEY, DEFAULT_BASE, MYSQL_URI, REDIS_HOST, REDIS_PORT, \
    REDIS_DB, REDIS_PWD, ROUND_DIGITS
from models.models import ExchangeRate


# setting up MySQL connection
engine = create_engine(MYSQL_URI)
session = Session(engine)


# setting up Redis connection
redis_db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                             password=REDIS_PWD, decode_responses=True)

def get_oxr_rate():
    """
    Calls OXR API to get current exchange rate for the currency
    :return: dict - API response
    """
    url = f'https://openexchangerates.org/api/latest.json?app_id={OXR_APIKEY}'
    r = requests.get(url)
    return r.json()


def limit_to_currency(currency):
    """
    Get from OXR API data for selected currency
    :param currency: str. 3-letter code: GBP, EUR.
        `currency` can't be USD since we converting from it.
    :return: dict - exchange rate for specific currency
    """
    data = get_oxr_rate()
    exchange_rate = data.pop('rates').get(currency)
    if not exchange_rate:
        logging.warning(f'Exchange rate for {DEFAULT_BASE} - {currency} not available in API.')
    else:
        rate = {
            'timestamp': int(time()),
            'base': data.get('base'),
            'currency': currency,
            'rate': exchange_rate
        }
        return rate


def calculate_final_amount(rate, original_amount):
    """
    Calculates final amount of money in USD and return updated rate dict.
    :param rate: dict. Currency rates obtained from OXR API
    :param original_amount - amount in USD which needs to be converted.
    :return: dict - updated rates with converted money
    """
    rate.update(
        {
            'original_amount': original_amount,
            'converted_amount': round(original_amount/rate.get('rate'), ROUND_DIGITS),
        }
    )


def save_to_mysql(rate):
    """
    Saves calculated data to MySQL database
    :param rate: dict. Exchange rate information
    """
    er = ExchangeRate(
        timestamp=rate.get('timestamp'),
        base='USD',
        currency=rate.get('currency'),
        rate=rate.get('rate'),
        original_amount=rate.get('original_amount'),
        converted_amount=rate.get('converted_amount'),
    )
    session.add(er)
    session.commit()


def save_to_redis(rate):
    """
    Saves calculated data to Redis cache
    :param rate: dict. Exchange rate information
    """
    key = f'{rate.get("timestamp")}-{rate.get("currency")}'
    redis_db.hmset(key, rate)


def grab_and_save_rate(currency, original_amount):
    """
    Call OXR API with provided values and save output to MySQL and Redis
    :param currency: str - 3-letter code: GBP, EUR.
        `currency` can't be USD since we converting from it.
    :param original_amount: float - - amount in USD which needs to be converted.
    """
    rate = limit_to_currency(currency)
    calculate_final_amount(rate, original_amount)
    save_to_mysql(rate)
    save_to_redis(rate)


def get_from_my_sql(n=None, currency=None):
    """
    Query MySQL to get last operations which match criteria.
    :param n: int - number of operations
    :param currency: str - 3-letter code. Currency of exchange
    :return: list - operations performed.
    """
    if n is None:
        n = 1
    if currency:
        ms_data = session.query(ExchangeRate).filter(ExchangeRate.currency == currency)\
        .order_by(desc(ExchangeRate.timestamp)).limit(n)
    else:
        ms_data = session.query(ExchangeRate).order_by(desc(ExchangeRate.timestamp)).limit(n)
    return [ms.serialize for ms in ms_data]


def get_from_redis(n=None, currency=None):
    """
    Query Redis to get last operations which match criteria.
    :param n: int - number of operations
    :param currency: str - 3-letter code. Currency of exchange
    :return: list - operations performed.
    """
    if n is None:
        n = 1
    if currency:
        keys = [k for k in redis_db.keys() if currency in k]
    else:
        keys = [k for k in redis_db.keys()]
    keys.sort(reverse=True)
    return [redis_db.hgetall(keys[i]) for i in range(n)]

def jsonify_data(n=None, currency=None):
    """
    Return jsonified response to be shown as API response
    :param n: int - number of operations
    :param currency: str - 3-letter code. Currency of exchange
    :return: json
    """
    validation_error = validate_data(n, currency)
    if validation_error:
        return validation_error
    return jsonify(MYSQL=get_from_my_sql(n, currency),
                   Redis=get_from_redis(n, currency))


def validate_data(n=None, currency=None):
    """
    Validates user input to see if we have enough data for it.
    :param n: int - number of operations
    :param currency: str - 3-letter code. Currency of exchange
    :return: json - JSON error message to be shown for user.
    """
    total_currency_records = 0
    if currency:
        total_currency_records = session.query(ExchangeRate).\
            filter(ExchangeRate.currency == currency).count()
    total_records = session.query(ExchangeRate).count()
    if n and currency and total_currency_records < n:
        logging.warning(f'Requested last {n} exchanges for {currency}. Data only for '
                        f'{total_currency_records}'
                        f' rates present')
        return jsonify(APIWarning=f'Too large number of exchange rates for {currency}. '
                                  f'Only {total_currency_records} rates present')
    elif n and total_records < n:
        logging.warning(f'Requested last {n} exchanges. Data only for {total_records} '
                        f'rates present')
        return jsonify(APIWarning=f'Too large number of exchange rates. Only '
                                  f'{total_records} rates present')
    elif currency and total_currency_records == 0:
        logging.warning(f'Exchange rates for {currency} were requested. No data in database.')
        return jsonify(APIWarning=f'There is no exchange rates for {currency} in database')
    elif total_records == 0:
        logging.warning('Exchange rates were requested. No data in database.')
        return jsonify(APIWarning='There is no exchange rates in database')
    else:
        return {}
