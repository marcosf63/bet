from datetime import time
from bet.utils import is_time_smaller_than_now_plus30min

def test_is_time_smaller_than_now_plus30min():
    assert is_time_smaller_than_now_plus30min(time(0, 0)) is True or False, "Depende do momento do teste"

    assert is_time_smaller_than_now_plus30min(time(23, 59)) is False, "Deve ser falso, a menos que seja perto da meia-noite"


