import pytest

from utils.grab_and_save import calculate_final_amount
from config.settings import ROUND_DIGITS

@pytest.fixture
def rate():
    return {
        'base': 'USD',
        'currency': 'RUB',
        'rate': 65.4583,
        'timestamp': 1549705945
    }


def test_converted_amount_has_required_decimals_count(rate):
    calculate_final_amount(rate, 66.1598)
    converted_amount = str(rate.get('converted_amount'))
    assert converted_amount[::-1].find('.') == ROUND_DIGITS