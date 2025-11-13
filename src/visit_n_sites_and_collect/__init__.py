__all__ = ["MainController"]


def __getattr__(name):
    if name == "MainController":
        from .main import MainController

        return MainController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
