import streamlit as st
import pandas as pd
import os
import google.generativeai as genai
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import re

# --- 1. THE CLASSIC SILVER UI ---
st.set_page_config(page_title="SenseiSQL", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0d11; color: #C0C0C0; font-family: 'serif'; }
    
    /* Centered CAPITAL Heading */
    .main-title {
        text-align: center;
        font-size: 55px;
        letter-spacing: 6px;
        color: #E5E4E2;
        text-shadow: 2px 2px 10px #000000;
        margin-top: -30px;
    }
    
    /* 5 Lines of Explanation */
    .sub-text {
        text-align: center;
        font-size: 15px;
        color: #8A8D91;
        margin-bottom: 30px;
        line-height: 1.8;
    }

    /* 3D Silver Rectangular Uploader */
    [data-testid="stFileUploadDropzone"] {
        background: linear-gradient(145deg, #bdbebf, #e6e7e8);
        border: 2px solid #C0C0C0 !important;
        border-radius: 8px;
        box-shadow: inset 2px 2px 5px #ffffff, 5px 5px 15px #000000;
        color: #1a1a1a !important;
    }

    /* Silver Lining for Tables */
    .stDataFrame {
        border: 1px solid #C0C0C0;
        border-radius: 4px;
    }
    
    /* Input Box styling */
    .stChatInputContainer { border: 1px solid #4B4E53; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. HEADER & INTRO ---
st.markdown('<h1 class="main-title">SENSEI SQL</h1>', unsafe_allow_html=True)
st.markdown("""
    <p class="sub-text">
    POWERED BY ADVANCED GENERATIVE AI FOR INSTANT DATA INSIGHTS.<br>
    UPLOAD ANY CSV FILE TO TRANSFORM RAW DATA INTO A QUERYABLE DATABASE.<br>
    ASK COMPLEX QUESTIONS IN PLAIN ENGLISH WITHOUT WRITING A SINGLE LINE OF CODE.<br>
    EXPLORE THOUSANDS OF RECORDS EFFORTLESSLY WITH OUR HIGH-SPEED INTERFACE.<br>
    THE SENSEI ANALYZES YOUR ENTIRE DATASET TO PROVIDE ACCURATE TRUTH IN SECONDS.
    </p>
""", unsafe_allow_html=True)

# --- 3. BRAIN INITIALIZATION ---
if api_key:
    genai.configure(api_key=api_key)
    # UPDATED: Using the '-latest' suffix to bypass the 404/v1beta error
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
else:
    st.error("API Key missing! Check Secrets.")
    st.stop()

# --- 4. LOGIC & FUNCTIONS ---
def clean_col(name):
    return re.sub(r'\W+', '_', name.strip().lower())

def get_gemini_sql(question, schema):
    prompt = f"Expert SQL assistant. Table: 'data_table'. Columns: {schema}. Task: Convert '{question}' to SQLite. ONLY SQL CODE, NO MARKDOWN."
    response = model.generate_content(prompt)
    return response.text.replace('```sql', '').replace('```', '').strip()

# --- 5. THE WORKFLOW ---
uploaded_file = st.file_uploader("", type="csv") # Empty label because title is above

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df.columns = [clean_col(c) for c in df.columns]
    
    engine = create_engine('sqlite:///:memory:')
    df.to_sql('data_table', engine, index=False)
    
    st.markdown("### 📊 DATA PREVIEW")
    st.dataframe(df, use_container_width=True, height=300)
    
    user_query = st.chat_input("Ask Sensei about this data...")
    
    if user_query:
        with st.spinner("Sensei is calculating..."):
            try:
                schema_str = ", ".join(df.columns)
                sql = get_gemini_sql(user_query, schema_str)
                with engine.connect() as conn:
                    result = pd.read_sql_query(text(sql), conn)
                
                st.code(sql, language="sql")
                st.dataframe(result, use_container_width=True)
            except Exception as e:
                st.error(f"Sensei stumbled: {e}")
