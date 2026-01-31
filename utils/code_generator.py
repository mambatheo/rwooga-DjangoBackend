"""
Random code generation utilities.

Provides functions to generate random numeric codes for verification purposes.
"""

from random import randint
from django.conf import settings


def random_with_N_digits(n: int = 6) -> int:
    """
    Generate a random number with exactly N digits.
    
    Args:
        n: Number of digits for the generated code (default: 6)
        
    Returns:
        Random integer with exactly n digits
        
    Example:
        >>> code = random_with_N_digits(6)
        >>> 100000 <= code <= 999999
        True
    """
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)
