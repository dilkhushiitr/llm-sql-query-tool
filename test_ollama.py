import streamlit as st
import pandas as pd
import sqlalchemy as SA
from sqlalchemy import inspect
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# ---------------------------
# Streamlit sidebar: DB info
# ---------------------------
st.sidebar.title("Database Connection")

u = st.sidebar.text_input("User", value="dilkhush.meena@greedygame.com")
password = st.sidebar.text_input("Password / Token", type="password")
host = st.sidebar.text_input("Host", value="127.0.0.1")
port = st.sidebar.number_input("Port", value=8082)
db = st.sidebar.text_input("Database", value="service_incent_offerwall_apps")

# ---------------------------
# Create SQLAlchemy engine
# ---------------------------
engine = SA.create_engine(f"postgresql+psycopg2://{u}:{password}@{host}:{port}/{db}")

# ---------------------------
# Inspect schema
# ---------------------------
insp = inspect(engine)
cols = insp.get_columns("reports", schema="public")
schema_text = "CREATE TABLE public.reports (\n  " + ",\n  ".join(
    f'"{c["name"]}" {c.get("type","TEXT")}' for c in cols
) + "\n);"

st.sidebar.subheader("Schema Preview")
st.sidebar.text(schema_text)

# ---------------------------
# Initialize LLM
# ---------------------------
llm = ChatOllama(model="mistral", temperature=0)

prompt = ChatPromptTemplate.from_template("""
You are a PostgreSQL SQL generator.
Rules:
- Use only the tables/columns in the schema.
- Return exactly one valid PostgreSQL SELECT; no comments or markdown.
- Avoid DDL/DML.

Schema:
{schema}

Question: {question}
SQL:
""")

chain = prompt | llm | StrOutputParser()

# ---------------------------
# SQL safety check
# ---------------------------
BAD = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|MERGE)\b", re.I)

def is_safe(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("select") and not BAD.search(sql)

# ---------------------------
# Repair SQL if needed
# ---------------------------
repair_prompt = ChatPromptTemplate.from_template("""
The SQL failed on PostgreSQL; fix it and return one SELECT.

Schema:
{schema}

Question:
{question}

Previous SQL:
{sql}

Error:
{error}
""")
repair_chain = repair_prompt | llm | StrOutputParser()

# ---------------------------
# Ask function
# ---------------------------
def ask(question: str, max_repairs: int = 1):
    sql = chain.invoke({"schema": schema_text, "question": question}).strip()
    st.write("**Generated SQL:**")
    st.code(sql, language="sql")
    
    if not is_safe(sql):
        st.error("Unsafe or non-SELECT SQL generated.")
        return pd.DataFrame()
    
    try:
        return pd.read_sql(sql, con=engine)
    except Exception as e:
        if max_repairs <= 0:
            st.error(f"SQL Execution Error: {str(e)}")
            return pd.DataFrame()
        repaired = repair_chain.invoke({
            "schema": schema_text, "question": question, "sql": sql, "error": str(e)
        }).strip()
        st.write("**Repaired SQL:**")
        st.code(repaired, language="sql")
        if not is_safe(repaired):
            st.error("Repaired SQL is unsafe.")
            return pd.DataFrame()
        return pd.read_sql(repaired, con=engine)

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("English to SQl generation using LLM")

question = st.text_input(
    "Enter your question for SQL generation", 
    "Total revenue_in_usd sum for app_id 1333 on date '2025-09-10'"
)

if st.button("Run Query"):
    if question:
        df = ask(question)
        if not df.empty:
            st.write("**Query Result:**")
            st.dataframe(df)
            output_col = df.columns[-1]  # last column is usually the SUM
            st.success(f"Output: {df[output_col].iloc[0]}")
        else:
            st.warning("No data found or query failed.")
