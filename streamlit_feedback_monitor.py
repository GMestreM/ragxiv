"""Simple streamlit dashboard for user feedback monitoring"""

import os
import pandas as pd
from dotenv import load_dotenv, dotenv_values
import streamlit as st
import altair as alt
from collections import Counter

from ragxiv.database import (
    open_db_connection,
    PostgresParams,
)
from ragxiv.config import get_config

load_dotenv(".env")

config = get_config()
if config:
    config_ingestion = config["ingestion"]
    config_rag = config["rag"]


st.set_page_config(
    page_icon="🎛",
    layout="wide",
    page_title="Feedback monitor - ragXiv",
)

postgres_connection_params = PostgresParams(
    host=os.environ["POSTGRES_HOST"],
    port=os.environ["POSTGRES_PORT"],
    user=os.environ["POSTGRES_USER"],
    pwd=os.environ["POSTGRES_PWD"],
    database=os.environ["POSTGRES_DB"],
)


@st.cache_resource
def open_connection():
    conn = open_db_connection(
        connection_params=postgres_connection_params, autocommit=True
    )
    return conn


conn = open_connection()


# Fetch data from the database
@st.cache_data(ttl=60)
def load_data():
    query = "SELECT * FROM user_feedback"
    df = pd.read_sql(query, conn)
    return df


df = load_data()

st.header("User feedback monitor - ragXiv", divider="grey", anchor=False)

# Chart 1: User Ratings Distribution
st.subheader("User Ratings Distribution")
ratings_count = df["thumbs"].value_counts(dropna=False)
ratings_count = ratings_count.rename(
    {1: "Thumbs Up", 0: "Thumbs Down", None: "No Rating"}
)
st.bar_chart(ratings_count)

# Chart 2: Feedback Over Time
st.subheader("Feedback Over Time")
df["feedback_timestamp"] = pd.to_datetime(df["feedback_timestamp"])
feedback_over_time = df.groupby(df["feedback_timestamp"].dt.date).size()
st.line_chart(feedback_over_time)

# Chart 3: Average Response Time
st.subheader("Average Response Time")
df["elapsed_time_seconds"] = df["elapsed_time"].apply(
    lambda x: x.total_seconds() if pd.notnull(x) else None
)
average_response_time = df.groupby(df["feedback_timestamp"].dt.date)[
    "elapsed_time_seconds"
].mean()
st.line_chart(average_response_time)

# Chart 4: Top Retrieved Documents
st.subheader("Top Retrieved Documents")
top_documents = df["documents_retrieved"].dropna().str.split(",").explode()
top_documents_count = top_documents.value_counts().head(10)
st.bar_chart(top_documents_count)

# Chart 5: Frequent User Queries
st.subheader("Frequent User Queries")
word_cloud = " ".join(df["user_question"].dropna())
word_freq = Counter(word_cloud.split()).most_common(10)
word_freq_df = pd.DataFrame(word_freq, columns=["Word", "Count"])
chart = (
    alt.Chart(word_freq_df).mark_bar().encode(x=alt.X("Word:N", sort="-y"), y="Count:Q")
)
st.altair_chart(chart, use_container_width=True)
