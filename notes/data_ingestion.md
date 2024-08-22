# Data ingestion

## Obtaining papers from arXiv

- Academic papers are retrieved from [arXiv](https://arxiv.org) using the [`arxiv` library](http://lukasschwab.me/arxiv.py/arxiv.html)
- Some examples about the Search function:
    - Search last 10 papers that **contain a keyword**:
        ```python
        # Search for the 10 most recent articles matching the keyword "quantum."
        search = arxiv.Search(
            query = "quantum",
            max_results = 10,
            sort_by = SortCriterion.SubmittedDate
        )
        ```
    - **Advanced searching** (use [arXiv API manual for reference](https://arxiv.org/help/api/user-manual#query_details)):
        ```python
        search = arxiv.Search(query = "au:del_maestro AND ti:checkerboard")
        ```
    - Retrieve paper **by ID**:
        ```python
        search_by_id = Search(id_list=["1605.08386v1"])
        ```
- [This undocumented API feature](https://groups.google.com/g/arxiv-api/c/mAFYT2VRpK0?pli=1) can be used to filter by specific dates, but I still don't know how to filter between a range of dates.


## Parsing papers

- Instead of parsing the raw content of pdfs, we will use the html versions of the papers
- HTML versions of arXiv papers [started on 01/12/2023](https://arxiv.org/html/2402.08954v1), so this POC will only use papers from that date onwards
- Once the html has been retrieved it is processed until is converted to a more readable content, such as markdown. [Library `markdownify`](https://python.langchain.com/v0.2/docs/integrations/document_transformers/markdownify/) is used for this task.