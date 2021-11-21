"""Module containing custom exceptions."""


class MismatchedTokenError(Exception):
    """
    Raised when the number of input tokens does not match the user config.

    Attributes:
        expected (int): number of input tokens in the user config.
        given (int): number of input tokens passed in.
    """

    def __init__(self, expected: int, given: int) -> None:
        """
        Initialise the exception.

        Args:
            expected (int): number of input tokens in the user config.
            given (int): number of input tokens passed in.
        """
        self.expected = expected
        self.given = given
        super().__init__()


class BasePathDoesNotExistError(Exception):
    """Raised if the base path does not exist."""


class TemplateFileNotFoundError(Exception):
    """Raised if the template file does not exist."""


class ScopedPageAlreadyExists(Exception):
    """Raised if the scoped page file already exists."""


class MissingConfigYML(Exception):
    """Raised if the config.yml file is missing."""


class EmptyConfigYML(Exception):
    """Raised if the config.yml file is empty."""


class ScopeNotFound(Exception):
    """Raised if the scope does not exist in the config.yml."""


class MandatoryKeyNotFound(Exception):
    """Raised if a mandatory key is not found in the config.yml."""
