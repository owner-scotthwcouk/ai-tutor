import streamlit as st
from google import genai
import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# --- Initialize Supabase ---
@st.cache_resource
def init_supabase():
    url = os.environ.get("SUPABASE_URL") or (st.secrets["SUPABASE_URL"] if "SUPABASE_URL" in st.secrets else "")
    key = os.environ.get("SUPABASE_KEY") or (st.secrets["SUPABASE_KEY"] if "SUPABASE_KEY" in st.secrets else "")
    
    if url and key:
        return create_client(url, key)
    return None

supabase = init_supabase()

# --- Fetch Gemini API Key ---
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY") or (st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else "")

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
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- Sidebar Navigation ---
with st.sidebar:
    st.header("Navigation")
    if st.button("Main App & Dashboard"):
        st.session_state['page'] = "App"
        st.rerun()
    if st.button("Legal (Privacy & Terms)"):
        st.session_state['page'] = "Legal"
        st.rerun()
        
    st.divider()
    
    if st.session_state['logged_in']:
        st.write(f"👤 **User:** {st.session_state.get('current_user', 'Student')}")
        if st.button("Log Out"):
            if supabase:
                supabase.auth.sign_out()
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

elif not st.session_state['logged_in']:
    st.title("🎓 Welcome to AI Tutor")
    st.write("Please log in or register to access the platform.")
    
    if not supabase:
        st.warning("⚠️ Supabase is not connected. Please add SUPABASE_URL and SUPABASE_KEY to your environment variables or Streamlit secrets.")
    
    tab1, tab2 = st.tabs(["Log In", "Register"])
    
    with tab1:
        st.subheader("Student Log In")
        login_email = st.text_input("Email", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            if not supabase:
                st.error("Cannot connect to database. Contact support.")
            else:
                try:
                    response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = login_email
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed. Please check your credentials or register.")
                
    with tab2:
        st.subheader("Create a New Account")
        reg_email = st.text_input("Email Address", key="reg_user")
        reg_password = st.text_input("Choose a Password (min 6 chars)", type="password", key="reg_pass")
        if st.button("Register"):
            if not supabase:
                st.error("Cannot connect to database. Contact support.")
            elif reg_email and len(reg_password) >= 6:
                try:
                    response = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                    st.success("Account successfully created! You can now log in using the 'Log In' tab.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")
            else:
                st.warning("Please provide a valid email and a password of at least 6 characters.")

else:
    st.title("🎓 AI Tutor: Practice & Dashboard")
    st.write(f"Welcome back, **{st.session_state.get('current_user', 'Student')}**!")
    
    app_tab, dash_tab = st.tabs(["📚 Practice Area", "📈 Supabase Dashboard"])
    
    with app_tab:
        subject = st.selectbox("Select Subject", ["Biology", "Chemistry", "Physics", "English", "Maths", "Technology"])
        difficulty = st.select_slider("Question Difficulty", options=["Easy", "Medium", "Hard"])
        text_input = st.text_area(f"Paste {subject} Study Text Here", height=200)

        if st.button("Generate Quiz", type="primary"):
            if not GEMINI_API_KEY:
                st.warning("API key missing. Add GOOGLE_API_KEY to your secrets or environment variables.")
            elif text_input:
                with st.spinner(f"Analyzing text and building {subject} quiz..."):
                    quiz_data = generate_quiz(text_input, difficulty, subject, GEMINI_API_KEY)
                    if quiz_data:
                        st.session_state['current_quiz'] = quiz_data
                        st.session_state['quiz_submitted'] = False
            else:
                st.warning("Please enter some text.")

        if 'current_quiz' in st.session_state:
            st.subheader("Today's Practice Test")
            with st.form("quiz_form"):
                user_answers = {}
                for i, q in enumerate(st.session_state['current_quiz']):
                    st.write(f"**{i+1}. {q['question']}**")
                    user_answers[i] = st.radio("Select an answer:", q['options'], key=f"q_{i}")
                
                submitted = st.form_submit_button("Submit Answers")
                
                if submitted:
                    st.session_state['quiz_submitted'] = True
                    score = sum(1 for i, q in enumerate(st.session_state['current_quiz']) if user_answers[i] == q['answer'])
                    
                    if supabase:
                        try:
                            supabase.table("quiz_results").insert({
                                "user_email": st.session_state['current_user'],
                                "subject": subject,
                                "score": score,
                                "total": len(st.session_state['current_quiz'])
                            }).execute()
                            st.success("Score successfully saved to your Supabase Dashboard!")
                        except Exception as e:
                            st.error(f"Could not save score to Supabase. Error: {e}")

            if st.session_state.get('quiz_submitted'):
                for i, q in enumerate(st.session_state['current_quiz']):
                    if user_answers[i] == q['answer']:
                        st.success(f"**{i+1}. Correct:** {q['rationale']}")
                    else:
                        st.error(f"**{i+1}. Incorrect:** The answer is {q['answer']}. {q['rationale']}")

    with dash_tab:
        st.subheader("Your Progress Tracker")
        if not supabase:
            st.warning("Connect Supabase to view your dashboard data.")
        else:
            try:
                response = supabase.table("quiz_results").select("*").eq("user_email", st.session_state['current_user']).execute()
                data = response.data
                
                if data:
                    total_quizzes = len(data)
                    total_correct = sum(row['score'] for row in data)
                    total_questions = sum(row['total'] for row in data)
                    accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    col1.metric("Quizzes Completed", total_quizzes)
                    col2.metric("Overall Accuracy", f"{accuracy:.1f}%")
                    
                    st.divider()
                    st.write("### Recent Quizzes")
                    for row in reversed(data):
                        st.write(f"- **{row['subject']}**: Scored {row['score']}/{row['total']}")
                else:
                    st.info("No quizzes completed yet. Take your first practice test to populate your dashboard!")
            except Exception as e:
                st.error("Error fetching dashboard data from Supabase. Make sure the 'quiz_results' table exists.")
