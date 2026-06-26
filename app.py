import streamlit as st
from google import genai
import os
import json

def generate_quiz(text_snippet, difficulty, subject, api_key):
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = f"""
        You are an expert GCSE and A-Level {subject} Tutor in the UK. Your goal is to test a student's understanding of the provided text according to strict UK exam board standards (such as AQA, Edexcel, and OCR).
        
        Read the text snippet below and generate a 3-question multiple choice practice test at a {difficulty} difficulty level.
        The questions should test both factual recall and conceptual application, mirroring the style of GCSE or A-Level exam questions.
        
        Return ONLY a valid JSON array of objects. Do not use markdown blocks or extra text. 
        Each object MUST have exactly these keys: 
        - 'question' (string)
        - 'options' (array of exactly 4 strings)
        - 'answer' (exact string from the options array)
        - 'rationale' (a 1-2 sentence explanation of WHY this is the correct answer, based on the text)
        
        Study Text:
        {text_snippet}
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        raw_text = response.text.strip()
        start_index = raw_text.find('[')
        end_index = raw_text.rfind(']') + 1
        
        if start_index != -1 and end_index != 0:
            json_string = raw_text[start_index:end_index]
            return json.loads(json_string)
        else:
            return json.loads(raw_text)
            
    except Exception as e:
        st.error(f"Failed to get AI response. Error: {e}")
        return []

st.set_page_config(page_title="AI Tutor (UK)", page_icon="🎓", layout="wide")

# --- Initialize Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = "App"

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("Navigation")
    if st.button("Main App"):
        st.session_state['page'] = "App"
        st.rerun()
    if st.button("Legal (Privacy & Terms)"):
        st.session_state['page'] = "Legal"
        st.rerun()
    
    st.divider()
    if st.session_state['logged_in']:
        if st.button("Log Out"):
            st.session_state['logged_in'] = False
            st.rerun()

# --- Page Router ---
if st.session_state['page'] == "Legal":
    st.title("⚖️ Legal Information")
    
    st.subheader("Privacy Policy (GDPR)")
    st.markdown("""
    **Company:** SHW Technical Services (Operating Edumaxim and AI Study Buddy)  
    **Last Updated:** June 2026

    At SHW Technical Services ("we," "us," or "our"), we are committed to protecting your privacy and ensuring the security of your personal data across all our platforms, including Edumaxim and AI Study Buddy. This policy explains how we collect, use, and protect your information in compliance with the General Data Protection Regulation (GDPR).
    
    1. Data We Collect
    - A. General Account & Billing Data: Identity, Contact, Financial, and Usage Data.
    - B. Edumaxim-Specific Data: Tutor Payout Data, Booking Data.
    - C. AI Study Buddy-Specific Data: Academic & Interaction Data (Chat logs, uploads, learning patterns).
    
    2. How We Use Your Data: To provide services, process payments, improve platforms, communicate with users, and ensure security.
    
    3. Data Sharing: Internal sharing between platforms and with trusted third-party processors (e.g., Stripe, cloud providers).
    
    4. Your Rights (GDPR): Access, Rectification, Erasure, Restriction & Objection, Data Portability. Contact scott@scott-hw.online.
    
    5. Data Security: Robust technical and organizational measures implemented.
    """)
    
    st.subheader("Terms of Service")
    st.markdown("""
    **Last Updated:** June 2026

    1. **Acceptance of Terms:** By accessing and using SHW Technical Services, you agree to these terms.
    2. **General User Conduct:** Do not harass, use for illegal purposes, or attempt to hack the platforms.
    3. **Edumaxim:** Marketplace terms apply; platform circumvention is prohibited.
    4. **AI Study Buddy:** Subscription-based. Users agree to use as a learning aid; not for academic dishonesty. Note: AI models may hallucinate; verify information.
    5. **Limitation of Liability:** SHW Technical Services is not liable for indirect or consequential damages.
    6. **Modifications:** We may modify these terms at any time with notice.
    """)

elif not st.session_state['logged_in']:
    st.title("🎓 Welcome to AI Tutor")
    st.write("Please log in to continue.")

else:
    st.title("🎓 AI Tutor: GCSE & A-Level Practice")
    st.write("Welcome back! Select your subject and paste your text below to get started.")
