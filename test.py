from logging import exception


def division(a, b):
    try:
        result = a/b
        return result
    except exception:
        raise ValueError()


division(10, 0)
