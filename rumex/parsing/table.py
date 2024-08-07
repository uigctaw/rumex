class TableExceptionError(Exception):
    pass


class BadTableLineError(TableExceptionError):
    pass


class InconsistentTableError(TableExceptionError):
    pass


def parse_table_line(line, *, delimiter):
    line = line.strip()

    if (
        len(line) < 2  # noqa: PLR2004
        or line[0] != delimiter
        or line[-1] != delimiter
    ):
        raise BadTableLineError(line)

    line = line[1:]

    escape_symbol = "\\"
    values = []
    current_value = []
    escape_next_symbol = False
    for symbol in line:
        if escape_next_symbol:
            current_value.append(symbol)
            escape_next_symbol = False
        elif symbol == delimiter:
            values.append("".join(current_value).strip())
            current_value = []
        elif symbol == escape_symbol:
            escape_next_symbol = True
        else:
            current_value.append(symbol)

    if current_value:  # Can happen if the last delimiter was escaped
        raise BadTableLineError(line)

    return tuple(values)
