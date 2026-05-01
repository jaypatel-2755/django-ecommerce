from django import template

register = template.Library()


@register.filter
def indian_currency(value):
    """
    Format numbers using Indian digit grouping.
    Example: 175000 -> 1,75,000.00
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        return value

    # Always keep 2 digits after decimal for prices
    whole_part, decimal_part = f"{number:.2f}".split(".")

    # Indian grouping: last 3 digits, then groups of 2
    if len(whole_part) > 3:
        last_three = whole_part[-3:]
        remaining = whole_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.insert(0, remaining)
        whole_part = ",".join(groups + [last_three])

    return f"{whole_part}.{decimal_part}"
