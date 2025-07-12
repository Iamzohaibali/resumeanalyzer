import streamlit as st
import requests
import pdfplumber
import re
import io
import os
from dotenv import load_dotenv

# ------------------ CONFIG ------------------
load_dotenv()  # Load .env file
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
MODEL = "gemini-2.0-flash"

st.set_page_config(page_title="Gemini Resume Reviewer", layout="centered")
st.title("📄 AI Resume Reviewer using Google Gemini")

# ------------------ FUNCTIONS ------------------

def extract_text_from_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        return "\n".join([page.extract_text() or "" for page in pdf.pages])

def call_gemini(prompt):
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY,
    }
    endpoint = f"{BASE_URL}/{MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    response = requests.post(endpoint, headers=headers, json=payload)

    if response.status_code == 200:
        data = response.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    else:
        return f"❌ Error {response.status_code}: {response.text}"

def extract_keywords(text):
    return list(set(re.findall(r'\b\w{5,}\b', text.lower())))

# ------------------ UI ------------------

uploaded_resume = st.file_uploader("📎 Upload your Resume (PDF)", type=["pdf"])
job_description = st.text_area("📝 Paste the Job Description")

if st.button("🔍 Analyze Resume", key="analyze_button"):
    if uploaded_resume and job_description:
        with st.spinner("Analyzing your resume using Gemini..."):

            resume_text = extract_text_from_pdf(uploaded_resume)

            # Feedback Prompt
            feedback_prompt = f"""
You are a professional resume reviewer and job coach.

Compare the resume with the job description and provide bullet-pointed feedback under the following categories:

1. ✅ Matching strengths  
2. ⚠️ Weak points or missing skills  
3. 🛠️ Suggestions to improve the resume for this job  
4. 💡 Extra ways to make it stand out (keywords, phrasing, formatting)

Resume:
\"\"\"{resume_text}\"\"\"

Job Description:
\"\"\"{job_description}\"\"\"
"""
            feedback = call_gemini(feedback_prompt)

            # Score Prompt
            score_prompt = f"""
You are a resume evaluator. Based on this resume and job description, give a score out of 100 with a short reason.

Resume:
\"\"\"{resume_text}\"\"\"

Job Description:
\"\"\"{job_description}\"\"\"

Output format:
Score: 88/100  
Reason: ...
"""
            score = call_gemini(score_prompt)

            # Keyword Comparison
            resume_keywords = extract_keywords(resume_text)
            jd_keywords = extract_keywords(job_description)
            missing = [kw for kw in jd_keywords if kw not in resume_keywords][:10]

        # Results
        st.subheader("📌 Gemini Feedback")
        st.markdown(feedback)

        st.subheader("📊 Resume Score")
        st.markdown(score)

        if missing:
            st.subheader("🔑 Missing Keywords")
            st.markdown(", ".join(missing))

        st.download_button(
            label="📥 Download Feedback",
            data=feedback + "\n\n" + score,
            file_name="resume_feedback.txt",
            mime="text/plain"
        )
    else:
        st.warning("⚠️ Please upload both resume and job description.")

# ------------------ FOOTER ------------------
st.markdown("---")
st.markdown("<div style='text-align: center;'>Developed by Zohaib</div>", unsafe_allow_html=True)
