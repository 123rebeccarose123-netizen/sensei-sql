import streamlit as st
import pandas as pd
import os
from groq import Groq
from sqlalchemy import create_engine, text
import re

# 1. INITIALIZATION
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Retrieve API Key safely
api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key missing! Add GOOGLE_API_KEY to Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. UI STYLING
st.set_page_config(page_title="SenseiSQL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0d11; color: #C0C0C0; font-family: 'serif'; }
    
    .main-title {
        text-align: center;
        font-size: 55px;
        letter-spacing: 6px;
        color: #ffffff;
        text-shadow: 
            0 0 10px #fff,
            0 0 20px #fff,
            0 0 40px #fff,
            2px 2px 0px #aaa,
            4px 4px 0px #888,
            6px 6px 0px #666;
        margin-top: -30px;
        font-weight: bold;
    }
    
    .sub-text {
        text-align: center;
        font-size: 15px;
        color: #8A8D91;
        margin-bottom: 30px;
        line-height: 1.8;
    }
    
    [data-testid="stFileUploadDropzone"] {
        background: transparent !important;
        border: 2px solid #ffffff !important;
        border-radius: 8px;
        box-shadow: 0 0 8px #ffffff, 0 0 16px #ffffff55;
        color: #ffffff !important;
    }
    
    [data-testid="stDataFrame"] {
        border: 2px solid #ffffff !important;
        box-shadow: 0 0 8px #ffffff, 0 0 16px #ffffff55;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">SENSEI SQL</h1>', unsafe_allow_html=True)
st.markdown('''
<p class="sub-text">
    📂 Upload any CSV file and let Sensei do the work.<br>
    💬 Ask questions in plain English — no SQL knowledge needed.<br>
    ⚡ Instantly get results, tables, and queries powered by AI.
</p>
''', unsafe_allow_html=True)

# 3. GROQ FUNCTION
def get_sql(question, schema):
    prompt = f"Convert to SQLite: '{question}'. Table:'data_table'. Cols:{schema}. SQL ONLY, no explanation, no markdown."
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        sql = response.choices[0].message.content.strip().replace('```sql', '').replace('```', '').replace(';', '').strip()
        return sql
    except Exception as e:
        raise Exception(f"Error: {str(e)}")

# 4. DATA WORKFLOW
uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = [re.sub(r'\W+', '_', c.strip().lower()) for c in df.columns]
    engine = create_engine('sqlite:///:memory:')
    df.to_sql('data_table', engine, index=False, if_exists='replace')

    st.dataframe(df, use_container_width=True)

    st.markdown("**✨ Try asking:**")
    col1, col2, col3, col4 = st.columns(4)
    suggestion = None
    with col1:
        if st.button("Show top 5 rows"):
            suggestion = "Show top 5 rows"
    with col2:
        if st.button("Count total rows"):
            suggestion = "Count total rows"
    with col3:
        if st.button("Show column names"):
            suggestion = "Show all column names"
    with col4:
        if st.button("Calculate average of all columns"):
            suggestion = "Calculate average of all columns"

    user_query = st.chat_input("Ask Sensei...")
    final_query = suggestion or user_query

    if final_query:
        with st.spinner("Calculating..."):
            try:
                schema = ", ".join(df.columns)
                sql = get_sql(final_query, schema)
                with engine.connect() as conn:
                    result = pd.read_sql_query(text(sql), conn)
                st.code(sql, language="sql")
                st.dataframe(result, use_container_width=True)
            except Exception as e:
                st.error(f"Error: {e}")
