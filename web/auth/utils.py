import random


def generate_temp_password(length=8):
    """
    Generates a random alphanumerical password of given length.
    Default length is 8
    """
    return ''.join(random.SystemRandom().choices(string.ascii_letters +
                                                 string.digits,
                                                 k=length))
