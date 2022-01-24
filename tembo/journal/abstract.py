"""Submodule containing the abstract factories to create Tembo pages."""

from __future__ import annotations

import pathlib
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING

import jinja2
from jinja2.exceptions import TemplateNotFound

import tembo.utils
from tembo import exceptions

if TYPE_CHECKING:
    from tembo.journal.pages import PageCreatorOptions


class PageCreator:
    """
    A PageCreator factory base class.

    This factory should implement methods to create [Page][tembo.journal.pages.Page] objects.

    !!! abstract
        This factory is an abstract base class and should be implemented for each
        [Page][tembo.journal.pages.Page] type.

    The methods

    - `_check_base_path_exists()`
    - `_convert_base_path_to_path()`
    - `_load_template()`

    are not abstract and are shared between all [Page][tembo.journal.pages.Page] types.
    """

    @abstractmethod
    def __init__(self, options: PageCreatorOptions) -> None:
        """
        When implemented this should initialise the `PageCreator` factory.

        Args:
            options (PageCreatorOptions): An instance of
                [PageCreatorOptions][tembo.journal.pages.PageCreatorOptions]

        !!! abstract
        This method is abstract and should be implemented for each
        [Page][tembo.journal.pages.Page] type.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def options(self) -> PageCreatorOptions:
        """
        When implemented this should return the `PageCreatorOptions` on the class.

        Returns:
            PageCreatorOptions: the instance of
                [PageCreatorOptions][tembo.journal.pages.PageCreatorOptions] set on the class.

        !!! abstract
        This method is abstract and should be implemented for each
        [Page][tembo.journal.pages.Page] type.
        """
        raise NotImplementedError

    @abstractmethod
    def create_page(self) -> Page:
        """
        When implemented this should create a `Page` object.

        Returns:
            Page: an implemented instance of [Page][tembo.journal.pages.Page] such as
                [ScopedPage][tembo.journal.pages.ScopedPage].

        !!! abstract
        This method is abstract and should be implemented for each
        [Page][tembo.journal.pages.Page] type.
        """
        raise NotImplementedError

    def _check_base_path_exists(self) -> None:
        """
        Check that the base path exists.

        Raises:
            exceptions.BasePathDoesNotExistError: raised if the base path does not exist.
        """
        if not pathlib.Path(self.options.base_path).expanduser().exists():
            raise exceptions.BasePathDoesNotExistError(
                f"Tembo base path of {self.options.base_path} does not exist."
            )

    def _convert_base_path_to_path(self) -> pathlib.Path:
        """
        Convert the `base_path` from a `str` to a `pathlib.Path` object.

        Returns:
            pathlib.Path: the `base_path` as a `pathlib.Path` object.
        """
        path_to_file = (
            pathlib.Path(self.options.base_path).expanduser()
            / pathlib.Path(self.options.page_path.replace(" ", "_")).expanduser()
            / self.options.filename.replace(" ", "_")
        )
        # check for existing `.` in the extension
        extension = (
            self.options.extension[1:]
            if self.options.extension[0] == "."
            else self.options.extension
        )
        # return path with a file
        return path_to_file.with_suffix(f".{extension}")

    def _load_template(self) -> str:
        """
        Load the template file.

        Raises:
            exceptions.TemplateFileNotFoundError: raised if the template file is specified but
                not found.

        Returns:
            str: the contents of the template file.
        """
        if self.options.template_filename is None:
            return ""
        if self.options.template_path is not None:
            converted_template_path = pathlib.Path(self.options.template_path).expanduser()
        else:
            converted_template_path = (
                pathlib.Path(self.options.base_path).expanduser() / ".templates"
            )

        file_loader = jinja2.FileSystemLoader(converted_template_path)
        env = jinja2.Environment(loader=file_loader, autoescape=True)

        try:
            loaded_template = env.get_template(self.options.template_filename)
        except TemplateNotFound as template_not_found:
            _template_file = f"{converted_template_path}/{template_not_found.args[0]}"
            raise exceptions.TemplateFileNotFoundError(
                f"Template file {_template_file} does not exist."
            ) from template_not_found
        return loaded_template.render()


class Page(metaclass=ABCMeta):
    """
    Abstract Page class.

    This interface is used to define a `Page` object.

    A `Page` represents a note/page that will be saved to disk.

    !!! abstract
        This object is an abstract base class and should be implemented for each `Page` type.
    """

    @abstractmethod
    def __init__(self, path: pathlib.Path, page_content: str) -> None:
        """
        When implemented this should initalise a Page object.

        Args:
            path (pathlib.Path): the full path of the page including the filename as a
                [Path][pathlib.Path].
            page_content (str): the contents of the page.

        !!! abstract
        This method is abstract and should be implemented for each `Page` type.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def path(self) -> pathlib.Path:
        """
        When implemented this should return the full path of the page including the filename.

        Returns:
            pathlib.Path: the path as a [Path][pathlib.Path] object.

        !!! abstract
        This property is abstract and should be implemented for each `Page` type.
        """
        raise NotImplementedError

    @abstractmethod
    def save_to_disk(self) -> tembo.utils.Success:
        """
        When implemented this should save the page to disk.

        Returns:
            tembo.utils.Success: A Tembo [Success][tembo.utils.__init__.Success] object.

        !!! abstract
        This method is abstract and should be implemented for each `Page` type.
        """
        raise NotImplementedError
