import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import re

# 1. INITIALIZATION
# load_dotenv() looks for your API key in the .env file
load_dotenv()
st.set_page_config(page_title="SenseiSQL", layout="wide")

# API Configuration
# Replace your old API Configuration section with this:
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # ... rest of your model setup
else:
    st.error("API Key not found! Please check your Streamlit Secrets.")

# 2. HELPER FUNCTIONS
def clean_col(name):
    # Replaces non-alphanumeric characters with underscores for SQL safety
    return re.sub(r'\W+', '_', name.strip().lower())

def get_gemini_sql(question, schema):
    prompt = f"""
    You are a SQL expert. Given a table 'data_table' with these columns: {schema}
    Convert this question to a SQLite query: {question}
    Return ONLY the SQL code. No markdown, no backticks.
    """
    response = model.generate_content(prompt)
    return response.text.replace('```sql', '').replace('```', '').strip()

# 3. INTERFACE
st.title("🥷 SenseiSQL")
st.markdown("Upload a CSV and ask your AI Twin to analyze it using SQL.")

uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file is not None:
    # Load and Clean Data
    df = pd.read_csv(uploaded_file)
    df.columns = [clean_col(c) for c in df.columns]
    
    # Create temporary database in memory (RAM-friendly for 4GB)
    engine = create_engine('sqlite:///:memory:')
    df.to_sql('data_table', engine, index=False)
    
    st.write("### Data Preview", df.head(3))
    
    # Chat Input for user queries
    user_query = st.chat_input("Ask Sensei about this data...")
    
    if user_query:
        with st.spinner("Sensei is analyzing..."):
            try:
                # Generate SQL using Gemini
                schema_str = ", ".join(df.columns)
                sql = get_gemini_sql(user_query, schema_str)
                
                # Execute SQL against the in-memory DB
                with engine.connect() as conn:
                    result = pd.read_sql_query(text(sql), conn)
                
                # Show Results
                st.code(sql, language="sql")
                st.subheader("Result")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Sensei stumbled: {e}")
