"""Submodule containing the factories & page objects to create Tembo pages."""

from __future__ import annotations

import pathlib
import re
from dataclasses import dataclass
from typing import Collection, Optional

import jinja2
import pendulum
from jinja2.exceptions import TemplateNotFound

import tembo.utils
from tembo import exceptions
from tembo.journal.abstract import Page, PageCreator


@dataclass
class PageCreatorOptions:
    """
    Options [dataclass][dataclasses.dataclass] to create a Page.

    This is passed to an implemented instance of [PageCreator][tembo.journal.pages.PageCreator]

    Attributes:
        base_path (str): The base path.
        page_path (str): The path of the page relative to the base path.
        filename (str): The filename of the page.
        extension (str): The extension of the page.
        name (str): The name of the scope.
        user_input (Collection[str] | None, optional): User input tokens.
        example (str | None, optional): User example command.
        template_path (str | None, optional): The path which contains the templates. This should
            be the full path and not relative to the base path.
        template_filename (str | None, optional): The template filename with extension relative
            to the template path.
    """

    base_path: str
    page_path: str
    filename: str
    extension: str
    name: str
    user_input: Optional[Collection[str]] = None
    example: Optional[str] = None
    template_path: Optional[str] = None
    template_filename: Optional[str] = None


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


class ScopedPageCreator(PageCreator):
    """
    Factory to create a scoped page.

    Attributes:
        base_path (str): base path of tembo.
        page_path (str): path of the page relative to the base path.
        filename (str): filename relative to the page path.
        extension (str): extension of file.
    """

    def __init__(self, options: PageCreatorOptions) -> None:
        """
        Initialise a `ScopedPageCreator` factory.

        Args:
            options (PageCreatorOptions): An instance of
                [PageCreatorOptions][tembo.journal.pages.PageCreatorOptions].
        """
        self._all_input_tokens: list[str] = []
        self._options = options

    @property
    def options(self) -> PageCreatorOptions:
        """
        Return the `PageCreatorOptions` instance set on the factory.

        Returns:
            PageCreatorOptions:
                An instance of [PageCreatorOptions][tembo.journal.pages.PageCreatorOptions].
        """
        return self._options

    def create_page(self) -> Page:
        """
        Create a [ScopedPage][tembo.journal.pages.ScopedPage] object.

        This method will

        - Check the `base_path` exists
        - Verify the input tokens match the number defined in the `config.yml`
        - Substitue the input tokens in the filepath
        - Load the template contents and substitue the input tokens

        Raises:
            exceptions.MismatchedTokenError: Raises
                [MismatchedTokenError][tembo.exceptions.MismatchedTokenError] if the number of
                input tokens does not match the number of unique input tokens defined.
            exceptions.BasePathDoesNotExistError: Raises
                [BasePathDoesNotExistError][tembo.exceptions.BasePathDoesNotExistError] if the
                base path does not exist.
            exceptions.TemplateFileNotFoundError: Raises
                [TemplateFileNotFoundError][tembo.exceptions.TemplateFileNotFoundError] if the
                template file is specified but not found.


        Returns:
            Page: A [ScopedPage][tembo.journal.pages.ScopedPage] object using the
                `PageCreatorOptions`.
        """
        try:
            self._check_base_path_exists()
        except exceptions.BasePathDoesNotExistError as base_path_does_not_exist_error:
            raise base_path_does_not_exist_error
        self._all_input_tokens = self._get_input_tokens()
        try:
            self._verify_input_tokens()
        except exceptions.MismatchedTokenError as mismatched_token_error:
            raise mismatched_token_error

        path = self._convert_base_path_to_path()
        path = pathlib.Path(self._substitute_tokens(str(path)))

        try:
            template_contents = self._load_template()
        except exceptions.TemplateFileNotFoundError as template_not_found_error:
            raise template_not_found_error
        if self.options.template_filename is not None:
            template_contents = self._substitute_tokens(template_contents)

        return ScopedPage(path, template_contents)

    def _get_input_tokens(self) -> list[str]:
        """Get the input tokens from the path & user template."""
        path = str(
            pathlib.Path(
                self.options.base_path,
                self.options.page_path,
                self.options.filename,
            )
            .expanduser()
            .with_suffix(f".{self.options.extension}")
        )
        template_contents = self._load_template()
        # get the input tokens from both the path and the template
        all_input_tokens = []
        for tokenified_string in (path, template_contents):
            all_input_tokens.extend(re.findall(r"(\{input\d*\})", tokenified_string))
        return sorted(list(set(all_input_tokens)))

    def _verify_input_tokens(self) -> None:
        """
        Verify the input tokens.

        The number of input tokens should match the number of unique input tokens defined in the
        path and the user's template.

        Raises:
            exceptions.MismatchedTokenError: Raises
                [MismatchedTokenError][tembo.exceptions.MismatchedTokenError] if the number of
                input tokens does not match the number of unique input tokens defined.
        """
        if len(self._all_input_tokens) > 0 and self.options.user_input is None:
            raise exceptions.MismatchedTokenError(expected=len(self._all_input_tokens), given=0)
        if self.options.user_input is None:
            return
        if len(self._all_input_tokens) != len(self.options.user_input):
            raise exceptions.MismatchedTokenError(
                expected=len(self._all_input_tokens),
                given=len(self.options.user_input),
            )

    def _substitute_tokens(self, tokenified_string: str) -> str:
        """For a tokened string, substitute input, name and date tokens."""
        tokenified_string = self.__substitute_input_tokens(tokenified_string)
        tokenified_string = self.__substitute_name_tokens(tokenified_string)
        tokenified_string = self.__substitute_date_tokens(tokenified_string)
        return tokenified_string

    def __substitute_input_tokens(self, tokenified_string: str) -> str:
        """
        Substitue the input tokens in a `str` with the user input.

        Args:
            tokenified_string (str): a string with input tokens.

        Returns:
            str: the string with the input tokens replaced by the user input.

        Examples:
            A `user_input` of `("monthly_meeting",)` with a `tokenified_string` of
            `/meetings/{input0}/` results in a string of `/meetings/monthly_meeting/`
        """
        if self.options.user_input is not None:
            for input_value, extracted_token in zip(
                self.options.user_input, self._all_input_tokens
            ):
                tokenified_string = tokenified_string.replace(
                    extracted_token, input_value.replace(" ", "_")
                )
        return tokenified_string

    def __substitute_name_tokens(self, tokenified_string: str) -> str:
        """Find any `{name}` tokens and substitute for the name value in a `str`."""
        name_extraction = re.findall(r"(\{name\})", tokenified_string)
        for extracted_input in name_extraction:
            tokenified_string = tokenified_string.replace(extracted_input, self.options.name)
        return tokenified_string

    @staticmethod
    def __substitute_date_tokens(tokenified_string: str) -> str:
        """Find any {d:%d-%M-%Y} tokens in a `str`."""
        # extract the full token string
        date_extraction_token = re.findall(r"(\{d\:[^}]*\})", tokenified_string)
        for extracted_token in date_extraction_token:
            # extract the inner %d-%M-%Y only
            strftime_value = re.match(r"\{d\:([^\}]*)\}", extracted_token)
            if strftime_value is not None:
                strftime_value = strftime_value.group(1)
                if isinstance(strftime_value, str):
                    tokenified_string = tokenified_string.replace(
                        extracted_token, pendulum.now().strftime(strftime_value)
                    )
        return tokenified_string


class ScopedPage(Page):
    """
    A page that uses substitute tokens.

    Attributes:
        page_content (str): the content of the page from the template.
    """

    def __init__(self, path: pathlib.Path, page_content: str) -> None:
        """
        Initalise a scoped page object.

        Args:
            path (pathlib.Path): a [Path][pathlib.Path] object of the page's filepath including
                the filename.
            page_content (str): the content of the page from the template.
        """
        self._path = path
        self.page_content = page_content

    def __str__(self) -> str:
        """
        Return a `str` representation of a `ScopedPage`.

        Examples:
            ```
            >>> str(ScopedPage(Path("/home/bob/tembo/meetings/my_meeting_0.md"), ""))
            ScopedPage("/home/bob/tembo/meetings/my_meeting_0.md")
            ```

        Returns:
            str: The `ScopedPage` as a `str`.
        """
        return f'ScopedPage("{self.path}")'

    @property
    def path(self) -> pathlib.Path:
        """
        Return the full path of the page.

        Returns:
            pathlib.path: The full path of the page as a [Path][pathlib.Path] object.
        """
        return self._path

    def save_to_disk(self) -> tembo.utils.Success:
        """
        Save the scoped page to disk and write the `page_content`.

        Raises:
            exceptions.ScopedPageAlreadyExists: Raises
                [ScopedPageAlreadyExists][tembo.exceptions.ScopedPageAlreadyExists] if the page already exists.

        Returns:
            tembo.utils.Success: A [Success][tembo.utils.__init__.Success] with the path of the
                ScopedPage as the message.
        """
        # create the parent directories
        scoped_page_file = pathlib.Path(self.path)
        scoped_page_file.parents[0].mkdir(parents=True, exist_ok=True)
        if scoped_page_file.exists():
            raise exceptions.ScopedPageAlreadyExists(f"{self.path} already exists")
        with scoped_page_file.open("w", encoding="utf-8") as scoped_page:
            scoped_page.write(self.page_content)
        return tembo.utils.Success(str(self.path))
