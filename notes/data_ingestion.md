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
- It seems that [this undocumented API feature](https://groups.google.com/g/arxiv-api/c/mAFYT2VRpK0?pli=1) can be used to filter by specific dates, but there is not clear method to filter between a range of dates.


## Parsing papers

- Instead of parsing the raw content of pdfs, we will use the html versions of the papers
- HTML versions of arXiv papers [started on 01/12/2023](https://arxiv.org/html/2402.08954v1), so this POC will only use papers from that date onwards.
- Processing:
    - HTML versions of arXiv papers contain the main body as the `<article>` tag
    - Class `ltx_authors` contains the authors, which has already been retrieved as metadata and is not relevant information for the RAG system, so it is deleted.
    - Class `ltx_bibliography` contains the bibliography, not relevant for the RAG system, so it is deleted.
    - Class `ltx_figure` contains figures, which cannot be used in our RAG system as it is, so they are deleted.
    - Class `ltx_appendix` contains appendices, which usually contain math and theorems' proofs, not relevant for the RAG system.
    - Math equations are removed, from class `ltx_equation` and tag `<math>`.
- Once the html has been retrieved it is processed until is converted to a more readable content, such as markdown. [Library `markdownify`](https://python.langchain.com/v0.2/docs/integrations/document_transformers/markdownify/) is used for this task.


## Chunking

- Before creating the embeddings for each article, the content must be splitted into chunks.

Resources:
- [5 levels of text splitting](https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb)
- [Splitting html files and saving chunks using langchain](https://stackoverflow.com/questions/78481278/splitting-html-file-and-saving-chunks-using-langchain)
