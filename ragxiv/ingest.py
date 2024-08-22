"""Fetch data from sources and store them into the knowledge base"""

import datetime
from typing import List, Optional, TypedDict
import arxiv
import requests
from bs4 import BeautifulSoup
from config import ARXIV_FIELDS
from markdownify import MarkdownConverter
from tqdm.auto import tqdm


class PaperID(TypedDict):
    id: str
    summary: str
    authors: List[str]
    entry_url: str
    published: datetime.datetime
    primary_category: str
    categories: List[str]


def retrieve_arxiv_metadata(
    fields: List = ARXIV_FIELDS,
    max_results: Optional[int] = None,
    initial_date: Optional[datetime.datetime] = None,
    last_date: Optional[datetime.datetime] = None,
    verbose: bool = False,
) -> List[PaperID]:
    """
    Fetch metadata from arXiv documents for the relevant fields and
    between given dates

    Args:
        fields (List, optional): ArXiv categories to search for. Defaults
            to ARXIV_FIELDS.
        max_results (int, optional): Maximum results to search for. To fetch
            every result available, set max_results=None. The API's limit is
            300,000 results per query.
        initial_date (Optional[datetime]): Initial publication date of the
            retrieved documents. Defaults to None
        last_date (Optional[datetime]): Last publication date of the
            retrieved documents. Defaults to None
        verbose (bool): If True, show progress with tqdm. Defaults to False


    Returns:
        List[PaperID]: List containing the metadata for the relevant documents
            retrieved
    """
    # Open arXiv client
    client = arxiv.Client(
        page_size=100,
        delay_seconds=3.0,
        num_retries=3,
    )

    # Build query for arXiv's API
    arxiv_query = " OR ".join([f"cat:{field}" for field in fields])

    search = arxiv.Search(
        query=arxiv_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    results = client.results(search)

    # Iterate results and store valid metadata
    metadata = []
    for result in tqdm(results) if verbose else results:
        if initial_date:
            # If published earlier than initial_date, ignore
            if result.published < initial_date:
                continue
        if last_date:
            # If published after last_date, ignore
            if result.published > last_date:
                continue

        paper = PaperID(
            id=result.entry_id,
            summary=result.summary,
            authors=[name.name for name in result.authors],
            entry_url=result.entry_id,
            published=result.published,
            primary_category=result.primary_category,
            categories=result.categories,
        )
        metadata.append(paper)

    return metadata


def paper_html_to_markdown(paper_id: PaperID, verbose: bool = False) -> str | None:
    """
    Fetch the html version of a paper, process it and return as Markdown format

    Args:
        paper_id (PaperID): Metadata of a single arXiv paper
        verbose (bool): If True, show progress with tqdm. Defaults to False

    Returns:
        str: Processed markdown text of the paper
    """
    # Try to fetch html version of paper
    url_html = paper_id["entry_url"].replace("/abs/", "/html/")
    results = requests.get(url_html)

    # If it does not exist, raise error
    if results.status_code != 200:
        if verbose:
            print(
                f"Unable to fetch {url_html}. Status code: {results.status_code} ({results.reason})"
            )
        return None

    # Parse html to find article
    soup = BeautifulSoup(results.text, "html.parser")
    article = process_html_paper(soup=soup)

    # Convert to markdown
    markdown_article = MarkdownConverter().convert_soup(soup=article)

    # Strip extra blank lines
    markdown_article = markdown_article.replace("\n\n\n", "\n\n").replace(
        "\n\n\n", "\n\n"
    )

    return markdown_article


def process_html_paper(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Parse article from raw html and remove unnecesary sections

    Args:
        soup (BeautifulSoup): Raw html retrieved from arXiv

    Returns:
        BeautifulSoup: Processed html after removing unnecesary
            sections
    """
    # Find relevant part of article
    article = soup.find("article")

    # Remove authors
    div_authors = article.find_all("div", class_="ltx_authors")
    if div_authors:
        for div_author in div_authors:
            div_author.decompose()

    # Remove bibliography
    section_bibliography = article.find("section", class_="ltx_bibliography")
    if section_bibliography:
        section_bibliography.decompose()

    # Remove appendix
    sections_appendix = article.find_all("section", class_="ltx_appendix")
    if sections_appendix:
        for section_appendix in sections_appendix:
            section_appendix.decompose()

    # Remove figures
    figures = article.find_all("figure", class_="ltx_figure")
    if figures:
        for figure in figures:
            figure.decompose()

    # Remove math equations
    equations = article.find_all("table", class_="ltx_equation")
    if equations:
        for equation in equations:
            equation.decompose()
    inline_equations = article.find_all("math")
    if inline_equations:
        for inline_equation in inline_equations:
            inline_equation.decompose()

    return article
