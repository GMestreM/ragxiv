"""
Retrieve html versions of articles, parse them and return them as markdown formatted

It assumes that script `get_arxiv_metadata.py` has already been executed
"""

import os
import sys
import numpy as np
import pandas as pd
from tqdm.auto import tqdm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from ragxiv.ingest import paper_html_to_markdown

METADATA_PATH = "metadata_all.csv"

metadata = pd.read_csv(METADATA_PATH, sep=";")
metadata = metadata.to_dict(orient="records")

missing_count = 0
markdown_text = []
# forbidden at 1109
for paper_id in tqdm(metadata, total=len(metadata)):
    article_markdown = paper_html_to_markdown(paper_id=paper_id, verbose=True)
    if article_markdown:
        dict_markdown = dict(id=paper_id["id"], article=article_markdown)
        markdown_text.append(dict_markdown)
    else:
        print(f"Unable to parse document {paper_id['id']}")
        missing_count += 1

print(f"Missing documents: {missing_count}/{len(metadata)}")
df = pd.DataFrame.from_dict(markdown_text)
df.loc[df["article"].notnull(), :].to_csv("article_markdown.csv", sep=";")
