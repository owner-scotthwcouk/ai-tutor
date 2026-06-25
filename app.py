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
        
        # Extract the JSON array from the response safely
        raw_text = response.text.strip()
        start_index = raw_text.find('[')
        end_index = raw_text.rfind(']') + 1
        
        if start_index != -1 and end_index != 0:
            json_string = raw_text[start_index:end_index]
            return json.loads(json_string)
        else:
            return json.loads(raw_text)
            
    except Exception as e:
        error_message = str(e)
        if "403" in error_message or "PERMISSION_DENIED" in error_message:
            st.error("Error: Your API key was denied access. Please create a new API key at Google AI Studio.")
        else:
            st.error(f"Failed to get AI response. Error: {e}")
        return []

st.set_page_config(page_title="AI Tutor (UK)", page_icon="🎓")

# --- Initialize Session State for Auth, History, and Billing ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_history' not in st.session_state:
    st.session_state['user_history'] = []
if 'quiz' not in st.session_state:
    st.session_state['quiz'] = []
if 'quiz_count' not in st.session_state:
    st.session_state['quiz_count'] = 0
if 'is_premium' not in st.session_state:
    st.session_state['is_premium'] = False

# --- Authentication Flow ---
if not st.session_state['logged_in']:
    st.title("🎓 Welcome to AI Tutor")
    st.write("Your personal AI tutor for UK GCSE & A-Level subjects.")
    
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Student Login")
        username = st.text_input("Username (Student Name)")
        password = st.text_input("Password", type="password")
        
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if st.button("Log In", use_container_width=True):
                if username and password:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.rerun()
                else:
                    st.warning("Please enter username and password.")
        with btn_col2:
            if st.button("Create Account", type="primary", use_container_width=True):
                if username and password:
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username
                    st.success("Account created!")
                    st.rerun()
                else:
                    st.warning("Please enter username and password.")
    st.stop() 

# --- Main App (Only visible if logged in) ---
st.title("🎓 AI Tutor: GCSE & A-Level Practice")
st.write(f"Welcome back, **{st.session_state.get('username', 'Student')}**! Upload your syllabus text to generate today's interactive quiz.")

# Sidebar for settings
with st.sidebar:
    st.header("Tutor Settings")
    
    st.write(f"👤 **Student:** {st.session_state.get('username')}")
    
    if st.session_state['is_premium']:
        st.success("⭐ Premium Member")
    else:
        st.warning(f"Free Quizzes Used: {st.session_state['quiz_count']} / 2")
        if st.button("Upgrade to Premium (£5.99/mo)"):
            st.session_state['is_premium'] = True
            st.rerun()
            
    if st.button("Log Out"):
        st.session_state['logged_in'] = False
        st.rerun()
        
    st.divider()
    api_key_input = st.text_input("Gemini API Key", type="password", value=os.environ.get("GOOGLE_API_KEY", ""))
    
    st.divider()
    subject = st.selectbox("Select Subject", ["Biology", "Chemistry", "Physics", "English", "Maths", "Technology"])
    difficulty = st.select_slider("Question Difficulty", options=["Easy (Recall)", "Medium (Comprehension)", "Hard (Application)"])

# --- Tabs for App and Dashboard ---
tab1, tab2 = st.tabs(["📚 Practice Area", "📈 My Progress Dashboard"])

with tab1:
    text_input = st.text_area(f"Paste {subject} Study Text Here (e.g., AQA, Edexcel, or CGP Revision Guide text)", height=200)

    if st.button("Generate Quiz", type="primary"):
        if st.session_state['quiz_count'] >= 2 and not st.session_state['is_premium']:
            st.error("Free trial limit reached. Please upgrade to Premium in the sidebar to continue.")
        elif not api_key_input:
            st.warning("Please enter your Gemini API Key in the sidebar.")
        elif text_input:
            with st.spinner(f"Analyzing text and building {subject} quiz..."):
                quiz_data = generate_quiz(text_input, difficulty, subject, api_key_input)
                if quiz_data:
                    st.session_state['quiz'] = quiz_data
                    st.session_state['score'] = 0
                    st.session_state['submitted'] = False
                    st.session_state['quiz_count'] += 1
        else:
            st.warning("Please enter some text.")

    if st.session_state['quiz']:
        st.subheader("Today's Practice Test")
        with st.form("quiz_form"):
            user_answers = {}
            for i, q in enumerate(st.session_state['quiz']):
                st.write(f"**{i+1}. {q['question']}**")
                user_answers[i] = st.radio("Select an answer:", q['options'], key=f"q_{i}")
            
            submitted = st.form_submit_button("Submit Answers")
            
            if submitted:
                st.session_state['submitted'] = True
                score = 0
                for i, q in enumerate(st.session_state['quiz']):
                    if user_answers[i] == q['answer']:
                        score += 1
                st.session_state['score'] = score
                
                st.session_state['user_history'].append({
                    "subject": subject,
                    "score": score,
                    "total": len(st.session_state['quiz'])
                })

        if st.session_state.get('submitted'):
            st.success(f"Score: {st.session_state['score']} / {len(st.session_state['quiz'])}")
            for i, q in enumerate(st.session_state['quiz']):
                if user_answers[i] == q['answer']:
                    st.success(f"**{i+1}. Correct:** {q['rationale']}")
                else:
                    st.error(f"**{i+1}. Incorrect:** The answer is {q['answer']}. {q['rationale']}")

with tab2:
    st.subheader("Progress Log")
    if not st.session_state['user_history']:
        st.write("No quizzes taken yet.")
    else:
        total_quizzes = len(st.session_state['user_history'])
        total_correct = sum([entry['score'] for entry in st.session_state['user_history']])
        total_questions = sum([entry['total'] for entry in st.session_state['user_history']])
        accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 0
        
        col1, col2 = st.columns(2)
        col1.metric("Quizzes Completed", total_quizzes)
        col2.metric("Overall Accuracy", f"{accuracy:.1f}%")
        
        for i, entry in enumerate(reversed(st.session_state['user_history'])):
            st.write(f"- **{entry['subject']}**: {entry['score']}/{entry['total']}")