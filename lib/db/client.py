"""Cached Supabase connection pool.

Uses the transaction pooler (port 6543) per the spec -- Streamlit reruns the
script on every interaction and would otherwise exhaust direct connections.
prepare_threshold=None disables server-side prepared statements, which the
transaction-mode pooler does not support across pooled connections.
"""

import streamlit as st
from psycopg_pool import ConnectionPool


@st.cache_resource
def get_pool() -> ConnectionPool:
    db_uri = st.secrets["supabase"]["db_uri"]
    pool = ConnectionPool(
        conninfo=db_uri,
        min_size=1,
        max_size=3,
        kwargs={"prepare_threshold": None, "autocommit": False},
    )
    pool.wait()
    return pool
