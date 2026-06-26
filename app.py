import streamlit as st
from google import genai
import os
import json
from supabase import create_client, Client

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

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
        You are an expert GCSE and A-Level {subject} Tutor in the UK. Your goal is to test a student's understanding of the provided text according to strict UK exam board standards.
        Read the text snippet below and generate a 3-question multiple choice practice test at a {difficulty} difficulty level.
        Return ONLY a valid JSON array of objects. Do not use markdown blocks or extra text. 
        Each object MUST have exactly these keys: 'question', 'options' (array of 4 strings), 'answer', 'rationale'.
        Study Text:
        {text_snippet}
        """
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        raw_text = response.text.strip()
        start_index = raw_text.find('[')
        end_index = raw_text.rfind(']') + 1
        
        if start_index != -1 and end_index != 0:
            return json.loads(raw_text[start_index:end_index])
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
    st.subheader("Terms of Service & Privacy Policy")
    st.write("Please refer to our legal documentation regarding Edumaxim and AI Study Buddy...")
    # (Your full legal text goes here)

elif not st.session_state['logged_in']:
    st.title("🎓 Welcome to AI Tutor")
    st.write("Please log in or register to access the platform.")
    
    tab1, tab2 = st.tabs(["Log In", "Register"])
    
    with tab1:
        login_email = st.text_input("Email", key="login_user")
        login_password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Log In"):
            if supabase:
                try:
                    response = supabase.auth.sign_in_with_password({"email": login_email, "password": login_password})
                    st.session_state['logged_in'] = True
                    st.session_state['current_user'] = login_email
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
                
    with tab2:
        reg_email = st.text_input("Email Address", key="reg_user")
        reg_password = st.text_input("Choose a Password (min 6 chars)", type="password", key="reg_pass")
        if st.button("Register"):
            if supabase and reg_email and len(reg_password) >= 6:
                try:
                    response = supabase.auth.sign_up({"email": reg_email, "password": reg_password})
                    st.success("Account created! Please log in.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")

else:
    st.title("🎓 AI Tutor: Practice & Dashboard")
    st.write(f"Welcome back, **{st.session_state.get('current_user', 'Student')}**!")
    
    app_tab, dash_tab = st.tabs(["📚 Practice Area", "📈 Supabase Dashboard"])
    
    with app_tab:
        # --- PAYWALL LOGIC ---
        free_limit = 2
        usage_count = 0
        
        if supabase:
            try:
                # Count how many quizzes the user has saved
                response = supabase.table("quiz_results").select("*").eq("user_email", st.session_state['current_user']).execute()
                usage_count = len(response.data) if response.data else 0
            except Exception as e:
                pass

        if usage_count >= free_limit:
            st.error("🚀 Free Trial Limit Reached!")
            st.markdown("""
            ### Upgrade to Premium
            You have completed your free practice tests. To continue generating unlimited A-Level and GCSE quizzes, unlock the full power of AI Study Buddy.
            
            * ✅ Unlimited daily quiz generation
            * ✅ Advanced analytics & gap identification
            * ✅ Priority curriculum updates
            """)
            
            # Note: Replace this # with your actual Stripe Payment Link!
            stripe_link = "https://buy.stripe.com/test_your_link_here" 
            st.markdown(f'<a href="{stripe_link}" target="_blank"><button style="background-color:#635BFF;color:white;padding:12px 24px;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer;">Subscribe Now ($15/mo)</button></a>', unsafe_allow_html=True)

        else:
            # Show normal UI if they are under the limit
            st.info(f"Free Quizzes Remaining: {free_limit - usage_count}")
            
            subject = st.selectbox("Select Subject", ["Biology", "Chemistry", "Physics", "English", "Maths", "Technology"])
            difficulty = st.select_slider("Question Difficulty", options=["Easy", "Medium", "Hard"])
            text_input = st.text_area(f"Paste {subject} Study Text Here", height=200)

            if st.button("Generate Quiz", type="primary"):
                if not GEMINI_API_KEY:
                    st.warning("API key missing. Add GOOGLE_API_KEY to your secrets.")
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
                                st.success("Score successfully saved! Your usage limit has been updated.")
                                # Clear the quiz from session state so the UI refreshes limits on next action
                                del st.session_state['current_quiz']
                            except Exception as e:
                                st.error(f"Could not save score to Supabase. Error: {e}")

    with dash_tab:
        st.subheader("Your Progress Tracker")
        if supabase:
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
                st.error("Error fetching dashboard data.")
