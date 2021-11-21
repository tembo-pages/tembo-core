"""Subpackage containing utility objects."""

from dataclasses import dataclass


@dataclass
class Success:
    """
    A Tembo success object.

    This is returned from [Page][tembo.journal.pages.ScopedPage] methods such as
    [save_to_disk()][tembo.journal.pages.ScopedPage.save_to_disk]

    Attributes:
        message (str): A success message.
    """

    message: str
