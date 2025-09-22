text
# LLM SQL Query Tool

Convert English questions into safe PostgreSQL SELECT queries using Streamlit, SQLAlchemy, pandas, and a local Ollama (Mistral) LLM. Results are shown in a Streamlit table with a simple “Output” summary.

## Features
- Schema-aware prompting from `public.reports` columns.
- LLM generates exactly one PostgreSQL SELECT (no DDL/DML).
- Regex safety gate blocks non-SELECT and dangerous keywords.
- Auto-repair: one retry with error details if SQL fails.
- Executes with `pandas.read_sql` on a SQLAlchemy engine.

## Architecture
flowchart LR
Q[User Question] --> UI[Streamlit UI]
UI --> INT[Schema Introspection\n(SQLAlchemy inspect)]
INT --> PROMPT[Prompt Template\n(ChatPromptTemplate)]
PROMPT --> LLM[Ollama + Mistral\n(ChatOllama)]
LLM --> SAFE[SQL Safety Check\n(SELECT-only regex)]
SAFE --> PG[PostgreSQL\n(pandas.read_sql + Engine)]
PG -->|OK| RES[Results\n(DataFrame + UI)]
PG -->|Error| REPAIR[Repair Chain\n(LLM fixes SQL)]
REPAIR --> SAFE

text

## Quickstart
1. Install:
pip install streamlit pandas sqlalchemy psycopg2-binary langchain-ollama langchain-core

text
2. Start Ollama and pull the model:
ollama pull mistral

text
3. Run:
streamlit run app.py

text
4. In the sidebar, set DB connection and ask:
Total revenue_in_usd sum for app_id 1333 on date '2025-09-10'

text

## Key snippets
Engine
engine = SA.create_engine("postgresql+psycopg2://USER:PASSWORD@HOST:PORT/DB")

Introspection
insp = inspect(engine)
cols = insp.get_columns("reports", schema="public")

Safety
BAD = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|REPLACE|MERGE)\b", re.I)
def is_safe(sql: str) -> bool:
s = sql.strip().lower()
return s.startswith("select") and not BAD.search(sql)

Execute
df = pd.read_sql(sql, con=engine)

text

## Notes
- Use read-only DB credentials; consider LIMIT and statement timeouts by default.
- Do not hardcode secrets; use environment variables or Streamlit’s password field.







### ✅ Explanation (non-technical):

1. **🙋 You** ask a question in plain English.  
2. **💻 Streamlit App** sends it to the AI model.  
3. **🤖 AI Model** converts the question into a database query (SQL).  
4. **🛡 Safety Check** makes sure the query is safe (only `SELECT`).  
5. If safe → runs on **🐘 Database**, and result comes back.  
6. **📊 Answer** is shown clearly in the app.  
7. If unsafe → query is **⚠️ blocked** to protect data.  
