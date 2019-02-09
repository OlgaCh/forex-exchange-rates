from models.models import ExchangeRate


def test_exchange_rate_model():
    test = ExchangeRate(
        timestamp=1234567,
        base='USD',
        currency='GBP',
        rate=0.12345,
        original_amount=1,
        converted_amount=0.12345
    )
    assert test.timestamp == 1234567
    assert test.base == 'USD'
    assert test.currency == 'GBP'
    assert test.rate == 0.12345
    assert test.original_amount == 1
    assert test.converted_amount == 0.12345

