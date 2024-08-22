"""Retrieve metadata from relevant arXiv papers"""

import datetime

import pandas as pd

from ragxiv.config import ARXIV_FIELDS
from ragxiv.ingest import retrieve_arxiv_metadata

initial_date = datetime.datetime(
    year=2023, month=12, day=1, tzinfo=datetime.timezone.utc
)
last_date = datetime.datetime(year=2024, month=8, day=14, tzinfo=datetime.timezone.utc)
metadata = retrieve_arxiv_metadata(
    initial_date=initial_date,
    last_date=last_date,
    max_results=100000,
    fields=ARXIV_FIELDS,
    verbose=True,
)

df = pd.DataFrame.from_dict(metadata)
df.to_csv(f"metadata_all_{datetime.datetime.today():%Y-%m-%d}.csv", sep=";")
