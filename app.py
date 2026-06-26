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

# --- Initialize Page State ---
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

# --- Page Router ---
if st.session_state['page'] == "Legal":
    st.title("⚖️ Legal Information")
    
    st.subheader("Privacy Policy (GDPR)")
    st.markdown("""
    **Company:** SHW Technical Services (Operating Edumaxim and AI Study Buddy)  
    **Last Updated:** June 2026

    At SHW Technical Services ("we," "us," or "our"), we are committed to protecting your privacy and ensuring the security of your personal data across all our platforms, including Edumaxim and AI Study Buddy. This policy explains how we collect, use, and protect your information in compliance with the General Data Protection Regulation (GDPR).

    **1. Data We Collect**
    We collect different types of information depending on which of our services you use:
    A. General Account & Billing Data (All Platforms): Identity Data (Name, DOB, photos), Contact Data (Email, phone), Financial Data (Processed via Stripe; we do not store full credit card numbers), and Usage Data.
    B. Edumaxim-Specific Data: Tutor Payout Data (bank details), Booking Data (session logs, communications).
    C. AI Study Buddy-Specific Data: Academic & Interaction Data (Chat logs, queries, document uploads, learning patterns).

    **2. How We Use Your Data**
    - To Provide Services: Facilitate bookings (Edumaxim); personalize learning and track progress (AI Study Buddy).
    - Financial Processing: Manage billing, refunds, and tutor payouts.
    - Platform Improvement: Analyze usage patterns. We remove personally identifiable information before using data to train generalized AI models.
    - Communication: Send service updates and support responses.
    - Security & Compliance: Prevent fraudulent activity.

    **3. Data Sharing and Transfers**
    Internal sharing between Edumaxim and AI Study Buddy for a seamless experience. Third-party processors (Stripe, cloud providers) operate under strict data processing agreements.

    **4. Your Rights (GDPR)**
    You have rights to Access, Rectification, Erasure ("Right to be Forgotten"), Restriction, Objection, and Data Portability. Contact our DPO at scott@scott-hw.online.

    **5. Data Security**
    We implement robust technical and organizational security measures to prevent unauthorized data access. Access is limited to authorized personnel subject to confidentiality obligations.
    """)
    
    st.subheader("Terms of Service")
    st.markdown("""
    **Last Updated:** June 2026

    **1. Acceptance of Terms**
    By accessing and using SHW Technical Services platforms, you accept and agree to be bound by these terms.

    **2. General User Conduct**
    Users agree not to harass others, use services for illegal purposes, or attempt to hack our infrastructure.

    **3. Service-Specific Terms: Edumaxim**
    - Platform Circumvention: Prohibited.
    - Cancellation Policy: Full refund if cancelled 24+ hours before. Non-refundable within 24 hours.
    - Disclaimer: We connect users but do not employ tutors and are not responsible for instructional quality or offline conduct.

    **4. Service-Specific Terms: AI Study Buddy**
    - Subscriptions: Recurring billing. No partial refunds for unused time.
    - Academic Integrity: Designed as a learning aid, not for plagiarism. Users agree not to violate their institution’s integrity policies.
    - AI Output Limitations: Models may "hallucinate." Users must verify factual information. Output does not constitute professional advice.

    **5. Limitation of Liability**
    SHW Technical Services and its subsidiaries shall not be liable for any indirect, incidental, special, consequential, or punitive damages (including loss of profits/data) arising from use or inability to use our services.

    **6. Modifications to the Terms**
    We reserve the right to modify these terms. Significant changes will be notified via email or platform notice. Continued use constitutes acceptance.
    """)

else:
    st.title("🎓 AI Tutor: GCSE & A-Level Practice")
    st.write("Welcome! Select your subject and paste your text below to get started.")
    # Application content starts here
