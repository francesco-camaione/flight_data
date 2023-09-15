from forex_python.converter import CurrencyRates
import re


def remove_spaces_and_digits(s: str) -> str:
    s_without_digits = s.replace(":", "").replace("-", "")
    return s_without_digits.replace(" ", "")


def pounds_to_euros(pounds: int) -> int:
    c = CurrencyRates()
    exchange_rate = c.get_rate('GBP', 'EUR')
    euros = pounds * exchange_rate
    return int(euros)


def extract_date_from_url(url):
    # Define a regular expression pattern to match the date after "when="
    date_pattern = r'when=(\d{4}-\d{2}-\d{2})'
    # Use re.search to find the date in the URL
    match = re.search(date_pattern, url)

    if match:
        # Extract the matched date
        date = match.group(1)
        return date
    else:
        return None


if __name__ == "__main__":
    print(pounds_to_euros(84))
