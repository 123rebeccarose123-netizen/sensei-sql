import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
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

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("API Key missing! Configure GOOGLE_API_KEY in Streamlit Secrets.")
    st.stop()

# 2. UI STYLING
st.set_page_config(page_title="SenseiSQL", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0b0d11; color: #C0C0C0; font-family: 'serif'; }
    .main-title { text-align: center; font-size: 55px; letter-spacing: 6px; color: #E5E4E2; text-shadow: 2px 2px 10px #000000; margin-top: -30px; }
    .sub-text { text-align: center; font-size: 15px; color: #8A8D91; margin-bottom: 30px; line-height: 1.8; }
    [data-testid="stFileUploadDropzone"] { background: linear-gradient(145deg, #bdbebf, #e6e7e8); border: 2px solid #C0C0C0 !important; border-radius: 8px; color: #1a1a1a !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<h1 class="main-title">SENSEI SQL</h1>', unsafe_allow_html=True)
#-----------
def get_gemini_sql(question, schema):
    prompt = f"Convert to SQLite: '{question}'. Table:'data_table'. Cols:{schema}. SQL ONLY."
    
    # Trying EVERY possible naming convention for your API key
    models_to_try = [
        'gemini-1.5-flash', 
        'gemini-1.0-pro', 
        'gemini-pro',
        'models/gemini-1.5-flash',
        'models/gemini-pro'
    ]
    
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            # This cleans the AI output so it's pure SQL
            sql = response.text.strip().replace('```sql', '').replace('```', '').replace(';', '')
            return sql
        except Exception:
            continue
            
    raise Exception("API Key connection failed. Please go to https://aistudio.google.com/ and create a NEW API Key.")

# 4. DATA WORKFLOW
uploaded_file = st.file_uploader("", type="csv") 

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = [re.sub(r'\W+', '_', c.strip().lower()) for c in df.columns]
    engine = create_engine('sqlite:///:memory:')
    df.to_sql('data_table', engine, index=False)
    
    st.dataframe(df.head(10), use_container_width=True)
    user_query = st.chat_input("Ask Sensei...")
    
    if user_query:
        with st.spinner("Calculating..."):
            try:
                schema = ", ".join(df.columns)
                sql = get_gemini_sql(user_query, schema)
                with engine.connect() as conn:
                    result = pd.read_sql_query(text(sql), conn)
                st.code(sql, language="sql")
                st.dataframe(result, use_container_width=True)
            except Exception as e:
                import google.generativeai as gai
                st.error(f"Error: {e}")
                st.info(f"System Check: Library Version {gai.__version__}")
