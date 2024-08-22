# Data ingestion

- Academic papers are retrieved from [arXiv](https://arxiv.org) using the [`arxiv` library](http://lukasschwab.me/arxiv.py/arxiv.html)
- Some examples about the Search function:
    - Search last 10 papers:
        ```python
        # Search for the 10 most recent articles matching the keyword "quantum."
        search = arxiv.Search(
            query = "quantum",
            max_results = 10,
            sort_by = SortCriterion.SubmittedDate
        )
        ```
    - Advanced searching (use [arXiv API manual for reference](https://arxiv.org/help/api/user-manual#query_details)):
        ```python
        search = arxiv.Search(query = "au:del_maestro AND ti:checkerboard")
        ```
    - Retrieve paper by ID:
        ```python
        search_by_id = Search(id_list=["1605.08386v1"])
        ```