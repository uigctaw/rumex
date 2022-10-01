from .runner import run


def _name_of(fn_or_cls):
    return fn_or_cls.__name__


__all__ = tuple(map(_name_of, (
    # ExecutedFile,
    # InputFile,
    run,
)))
