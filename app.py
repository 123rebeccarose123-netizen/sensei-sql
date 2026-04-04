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

api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key missing! Add GOOGLE_API_KEY to Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. UI STYLING
st.set_page_config(page_title="SenseiSQL", layout="wide")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

dark = st.session_state.dark_mode

if dark:
    bg = "#0d1826"
    neu_shadow = "8px 8px 18px #07101a, -8px -8px 18px #132032"
    neu_shadow_sm = "5px 5px 12px #07101a, -5px -5px 12px #132032"
    table_shadow = "6px 6px 16px #07101a, -6px -6px 16px #132032, 0 0 0 1.5px #87ceeb, 0 0 12px #87ceeb55"
    chat_shadow = "6px 6px 16px #07101a, -6px -6px 16px #132032, 0 0 0 1.5px #87ceeb55"
    btn_shadow = "5px 5px 12px #07101a, -5px -5px 12px #132032, 0 0 8px #87ceeb44, inset 0 0 0 1px #87ceeb33"
    upload_border = "1.5px dashed #87ceeb"
    upload_inset = "inset 4px 4px 10px #07101a, inset -4px -4px 10px #132032"
    text_color = "#a8cfe0"
    label_color = "#7ab8d9"
    title_shadow = "0 0 10px #fff, 0 0 20px #fff, 2px 2px 0 #aaa, 4px 4px 0 #888"
    title_color = "#ffffff"
    subtitle_color = "#7ab8d9"
    th_bg = "#112233"
    th_color = "#87ceeb"
    td_bg = "#0d1826"
    td_color = "#a8cfe0"
    td_border = "#1a2e40"
    upload_text = "#87ceeb"
    btn_label = "☀️ Light Mode"
else:
    bg = "#d6eef8"
    neu_shadow = "8px 8px 18px #b0cfe0, -8px -8px 18px #f8ffff"
    neu_shadow_sm = "5px 5px 12px #b0cfe0, -5px -5px 12px #f8ffff"
    table_shadow = "6px 6px 16px #b0cfe0, -6px -6px 16px #f8ffff"
    chat_shadow = "6px 6px 16px #b0cfe0, -6px -6px 16px #f8ffff"
    btn_shadow = "5px 5px 12px #b0cfe0, -5px -5px 12px #f8ffff"
    upload_border = "1.5px dashed #5a9abf"
    upload_inset = "inset 4px 4px 10px #b0cfe0, inset -4px -4px 10px #f8ffff"
    text_color = "#1a3a5a"
    label_color = "#1a4a7a"
    title_shadow = "2px 2px 0 #b0cfe8, 4px 4px 0 #90b8d8"
    title_color = "#0a2a4a"
    subtitle_color = "#2a5a8a"
    th_bg = "#b8ddf0"
    th_color = "#0a2a4a"
    td_bg = "#d6eef8"
    td_color = "#1a3a5a"
    td_border = "#b8ddf0"
    upload_text = "#2a6a9a"
    btn_label = "🌙 Dark Mode"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {bg} !important; }}
    .main-title {{
        text-align: center; font-size: 55px; letter-spacing: 6px;
        font-weight: bold; color: {title_color};
        text-shadow: {title_shadow};
        margin-top: -30px; margin-bottom: 10px;
    }}
    .sub-text {{
        text-align: center; font-size: 15px; color: {subtitle_color};
        margin-bottom: 30px; line-height: 2;
    }}
    .neu-card {{
        background: {bg}; border-radius: 18px;
        box-shadow: {neu_shadow}; padding: 22px; margin-bottom: 22px;
    }}
    .upload-label {{
        font-size: 13px; color: {label_color};
        margin-bottom: 10px; display: block;
    }}
    .upload-box {{
        border-radius: 14px; border: {upload_border};
        box-shadow: {upload_inset};
        padding: 28px; text-align: center;
        color: {upload_text}; font-size: 13px;
    }}
    [data-testid="stFileUploadDropzone"] {{
        background: {bg} !important;
        border: {upload_border} !important;
        border-radius: 14px !important;
        box-shadow: {upload_inset} !important;
        color: {upload_text} !important;
    }}
    [data-testid="stDataFrame"] {{
        border-radius: 14px !important;
        box-shadow: {table_shadow} !important;
        overflow: hidden !important;
    }}
    .stButton > button {{
        background: {bg} !important;
        color: {th_color} !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: {btn_shadow} !important;
        padding: 10px 16px !important;
        font-size: 12px !important;
        transition: all 0.2s !important;
    }}
    .stButton > button:active {{
        box-shadow: inset 3px 3px 8px rgba(0,0,0,0.3) !important;
    }}
    .stChatInput > div {{
        background: {bg} !important;
        border-radius: 14px !important;
        box-shadow: {chat_shadow} !important;
        border: none !important;
    }}
    p, div, span, label {{ color: {text_color} !important; }}
    </style>
""", unsafe_allow_html=True)

# TOGGLE BUTTON
col_spacer, col_btn = st.columns([10, 1])
with col_btn:
    st.button(btn_label, on_click=toggle_theme)

st.markdown(f'<h1 class="main-title">SENSEI SQL</h1>', unsafe_allow_html=True)
st.markdown(f'''
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
