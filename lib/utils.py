from forex_python.converter import CurrencyRates


def remove_spaces_and_digits(s: str) -> str:
    s_without_digits = s.replace(":", "").replace("-", "")
    return s_without_digits.replace(" ", "")


def pounds_to_euros(pounds: int) -> int:
    c = CurrencyRates()
    exchange_rate = c.get_rate('GBP', 'EUR')
    euros = pounds * exchange_rate
    return int(euros)


if __name__ == "__main__":
    print(pounds_to_euros(84))
