from random import randint

from django.conf import settings


def random_with_N_digits(n=6):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)
