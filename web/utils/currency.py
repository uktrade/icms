# TODO: Revisit this when we know how to calculate it.
def get_euro_exchange_rate() -> float:
    return 1.11


def convert_gbp_to_euro(value_gbp: int) -> int:
    """Convert GBP to euros to the nearest euro."""
    exchange_rate = get_euro_exchange_rate()

    return round(value_gbp * exchange_rate, ndigits=None)
