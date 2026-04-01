import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import re

# 1. METALLIC NOIR FRONTEND
st.set_page_config(page_title="SenseiSQL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; color: #C0C0C0; }
    [data-testid="stSidebar"] { background-color: #1c1f26; border-right: 1px solid #4B4E53; }
    .stButton>button { background-color: #4B4E53; color: white; border-radius: 5px; border: 1px solid #C0C0C0; }
    .stAlert { background-color: #262730; color: #C0C0C0; border: 1px solid #C0C0C0; }
    </style>
    """, unsafe_allow_html=True)

# 2. INITIALIZATION
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("API Key not found! Please check your Streamlit Secrets.")
    st.stop()

# 3. HELPER FUNCTIONS
def clean_col(name):
    return re.sub(r'\W+', '_', name.strip().lower())

def get_gemini_sql(question, schema):
    prompt = f"You are a SQL expert. Given a table 'data_table' with these columns: {schema}. Convert this to a SQLite query: {question}. Return ONLY the SQL code."
    response = model.generate_content(prompt)
    return response.text.replace('```sql', '').replace('```', '').strip()

# 4. INTERFACE
st.title("🥷 SenseiSQL")
uploaded_file = st.file_uploader("Upload CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = [clean_col(c) for c in df.columns]
    
    # Create the SQL Engine (Crucial step!)
    engine = create_engine('sqlite:///:memory:')
    df.to_sql('data_table', engine, index=False)
    
    st.subheader("📊 Full Data Explorer")
    st.dataframe(df, use_container_width=True, height=300)
    st.write(f"**Total Records:** {len(df)}")

    user_query = st.chat_input("Ask Sensei about this data...")
    
    if user_query:
        with st.spinner("Sensei is analyzing..."):
            try:
                schema_str = ", ".join(df.columns)
                sql = get_gemini_sql(user_query, schema_str)
                
                with engine.connect() as conn:
                    result = pd.read_sql_query(text(sql), conn)
                
                st.code(sql, language="sql")
                st.subheader("Result")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Sensei stumbled: {e}")
