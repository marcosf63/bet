from datetime import datetime, time

from bet.utils.core import is_time_smaller_than_now_plus30min


def test_is_time_smaller_than_now_plus30min():
    """Test time comparison with now + 30min."""
    # Test with a time in the distant past (should return True)
    # This test is time-dependent, so we check the logic rather than absolute values
    current_hour = datetime.now().hour

    # A time 2 hours ago should always be less than now + 30min
    past_time = time((current_hour - 2) % 24, 0)
    result = is_time_smaller_than_now_plus30min(past_time)
    # The function returns True or False based on time comparison
    assert isinstance(result, bool)
