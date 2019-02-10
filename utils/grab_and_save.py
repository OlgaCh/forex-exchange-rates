import requests
import logging
import redis
from time import time

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config.settings import OXR_APIKEY, DEFAULT_BASE, MYSQL_URI, REDIS_HOST, REDIS_PORT, \
    REDIS_DB, REDIS_PWD, ROUND_DIGITS
from models.models import ExchangeRate


# setting up MySQL connection
engine = create_engine(MYSQL_URI)
session = Session(engine)


# setting up Redis connection
redis_db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PWD)


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
    rate = limit_to_currency(currency)
    calculate_final_amount(rate, original_amount)
    save_to_mysql(rate)
    save_to_redis(rate)
