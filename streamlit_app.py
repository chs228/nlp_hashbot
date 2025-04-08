import re
import streamlit as st
import io
import base64
import json
import requests
import os
import random
from datetime import datetime

# For PDF and DOCX processing
try:
    import PyPDF2
except ImportError:
    st.error("PyPDF2 is not installed. Please install it with: pip install PyPDF2")

try:
    import docx
except ImportError:
    st.error("python-docx is not installed. Please install it with: pip install python-docx")

# For email and PDF generation
from fpdf import FPDF
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Define skills dictionary
COMMON_SKILLS = {
    'programming': ['python', 'java', 'javascript', 'html', 'css', 'c++', 'c#', 'ruby', 'php', 'sql', 'r'],
    'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express', '.net'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis'],
    'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes'],
    'tools': ['git', 'github', 'jira', 'jenkins', 'agile', 'scrum'],
    'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 'time management'],
}

# Define custom technical questions based on skills
TECHNICAL_QUESTIONS = {
    'python': [
        {"question": "Explain how you would implement a decorator in Python.", 
         "expected_keywords": ["function", "wrapper", "decorator", "@", "arguments", "return"]},
        {"question": "How would you handle exceptions in Python?", 
         "expected_keywords": ["try", "except", "finally", "raise", "error", "handling"]},
        {"question": "Describe the difference between a list and a tuple in Python.", 
         "expected_keywords": ["mutable", "immutable", "list", "tuple", "ordered", "elements"]}
    ],
    'java': [
        {"question": "Explain the concept of inheritance in Java.", 
         "expected_keywords": ["extends", "class", "parent", "child", "super", "override"]},
        {"question": "How do you handle exceptions in Java?", 
         "expected_keywords": ["try", "catch", "finally", "throw", "throws", "exception"]},
        {"question": "What is the difference between an interface and an abstract class in Java?", 
         "expected_keywords": ["implement", "extend", "methods", "abstract", "interface", "multiple"]}
    ],
    'javascript': [
        {"question": "Explain closures in JavaScript.", 
         "expected_keywords": ["function", "scope", "variable", "closure", "lexical", "access"]},
        {"question": "How does asynchronous programming work in JavaScript?", 
         "expected_keywords": ["promise", "async", "await", "callback", "then", "event loop"]},
        {"question": "What's the difference between var, let, and const in JavaScript?", 
         "expected_keywords": ["scope", "hoisting", "reassign", "block", "function", "declaration"]}
    ],
    'sql': [
        {"question": "Explain the difference between INNER JOIN and LEFT JOIN.", 
         "expected_keywords": ["inner", "left", "join", "matching", "all", "records"]},
        {"question": "How would you optimize a slow SQL query?", 
         "expected_keywords": ["index", "execution plan", "query", "optimize", "performance", "analyze"]},
        {"question": "What is database normalization?", 
         "expected_keywords": ["normal form", "redundancy", "dependency", "relation", "table", "normalize"]}
    ],
    'react': [
        {"question": "Explain the component lifecycle in React.", 
         "expected_keywords": ["mount", "update", "unmount", "render", "effect", "component"]},
        {"question": "How do you manage state in React applications?", 
         "expected_keywords": ["useState", "useReducer", "state", "props", "context", "Redux"]},
        {"question": "What are hooks in React and why were they introduced?", 
         "expected_keywords": ["hooks", "functional", "state", "effect", "rules", "useState"]}
    ],
    'aws': [
        {"question": "Explain the difference between EC2 and Lambda.", 
         "expected_keywords": ["instance", "serverless", "EC2", "Lambda", "scaling", "compute"]},
        {"question": "How do you handle security in AWS?", 
         "expected_keywords": ["IAM", "security group", "encryption", "access", "policy", "role"]},
        {"question": "Describe the AWS services you've worked with.", 
         "expected_keywords": ["S3", "EC2", "Lambda", "RDS", "CloudFront", "DynamoDB"]}
    ],
}

# Add generic questions that can be asked for any role
GENERIC_QUESTIONS = [
    {"question": "Tell me about a challenging project you worked on and how you overcame obstacles.", 
     "expected_keywords": ["challenge", "project", "solution", "overcome", "team", "result"]},
    {"question": "How do you approach learning new technologies?", 
     "expected_keywords": ["learning", "research", "practice", "curiosity", "documentation", "projects"]},
    {"question": "Describe your experience with agile development methodologies.", 
     "expected_keywords": ["agile", "scrum", "sprint", "kanban", "standup", "retrospective"]},
    {"question": "How do you ensure code quality in your projects?", 
     "expected_keywords": ["testing", "review", "standards", "documentation", "refactoring", "clean"]}
]

# Chatbot welcome messages and prompts
WELCOME_MESSAGES = [
    "Welcome to TechInterviewBot! I'm here to help you practice your technical interview skills.",
    "Hello! I'm your Technical Interview Assistant. Let's prepare you for your next tech interview.",
    "Hi there! Ready to sharpen your technical interview skills? I'm here to help you practice.",
    "Welcome aboard! I'm your AI interview coach. Let's see how well you can handle technical questions."
]

RESUME_PROMPTS = [
    "To get started, please upload your resume or paste its content so I can tailor questions to your skills.",
    "Let's begin by analyzing your resume. Please upload it or paste the text so I can customize the interview.",
    "First, I'll need to see your resume to generate relevant questions. Upload a file or paste the text below.",
    "To create a personalized interview experience, I need to review your resume first. Upload or paste it below."
]

SKILL_MESSAGES = [
    "Great! I've analyzed your resume and identified these key skills:",
    "Thanks for sharing your resume! Based on my analysis, here are the skills I've identified:",
    "Perfect! After reviewing your resume, I've extracted these technical skills:",
    "I've processed your resume and found these skills that we can focus on:"
]

INTERVIEW_START_MESSAGES = [
    "Now let's begin the interview! I'll ask you a series of technical questions related to your skills.",
    "Ready to start? I've prepared some technical questions based on your experience.",
    "Let's dive into the technical interview! I'll ask questions related to your strongest skills.",
    "The interview is about to begin! I'll evaluate your answers to help improve your skills."
]

QUESTION_TRANSITIONS = [
    "Let's move on to the next question:",
    "Here's another question for you:",
    "Now, I'd like to ask you about:",
    "Let's continue with this question:",
    "For the next question:",
    "Moving forward:",
]

EVALUATION_POSITIVE = [
    "Great answer! You've covered the key points effectively.",
    "Excellent response! Your understanding of the concept is clear.",
    "Well done! Your explanation was thorough and accurate.",
    "Very good! You demonstrated strong knowledge in this area."
]

EVALUATION_AVERAGE = [
    "Good attempt! You covered some key points, but there's room for improvement.",
    "That's a decent answer, but you could expand on a few concepts.",
    "Not bad! You have the basic understanding, but consider adding more depth.",
    "You're on the right track, but try to be more specific in your explanations."
]

EVALUATION_NEEDS_IMPROVEMENT = [
    "You've made an attempt, but there are some key concepts missing.",
    "Your answer needs more technical depth. Let me suggest some areas to focus on.",
    "I see you have some understanding, but there are important points you didn't address.",
    "This response could be improved by including more specific technical details."
]

# Gemini API functions
def validate_answer_with_gemini(question, answer, expected_keywords):
    """
    Use Google's Gemini API to validate a candidate's answer.
    """
    api_key = os.environ.get("GEMINI_API_KEY", st.secrets.get("GEMINI_API_KEY", ""))
    
    if not api_key:
        st.warning("Gemini API key not found. Validation will be simulated.")
        keyword_count = sum(1 for keyword in expected_keywords if keyword.lower() in answer.lower())
        score = min(keyword_count / len(expected_keywords), 1.0) * 100
        return {
            "score": score,
            "feedback": "This is simulated feedback. Please configure Gemini API for actual validation.",
            "missing_concepts": [k for k in expected_keywords if k.lower() not in answer.lower()]
        }
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    prompt = f"""
    Question: {question}
    
    Candidate's Answer: {answer}
    
    Expected keywords or concepts: {', '.join(expected_keywords)}
    
    Evaluate this answer based on the following criteria:
    1. Presence of expected keywords/concepts
    2. Technical accuracy
    3. Clarity of explanation
    
    Provide:
    1. A score out of 100
    2. Brief feedback (2-3 sentences)
    3. List of any missing important concepts
    
    Format as JSON with keys: "score", "feedback", "missing_concepts"
    """
    
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        response_data = response.json()
        generated_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        
        json_str = ""
        json_started = False
        
        for line in generated_text.split("\n"):
            if line.strip() == "```json":
                json_started = True
                continue
            elif line.strip() == "```" and json_started:
                break
            elif json_started:
                json_str += line + "\n"
        
        if not json_str:
            json_str = generated_text
        
        json_str = json_str.replace("```json", "").replace("```", "").strip()
        
        try:
            result = json.loads(json_str)
            if "score" not in result:
                result["score"] = 50
            if "feedback" not in result:
                result["feedback"] = "No specific feedback provided."
            if "missing_concepts" not in result:
                result["missing_concepts"] = []
            return result
        except json.JSONDecodeError:
            return {
                "score": 50,
                "feedback": "Unable to parse evaluation. The answer may be incomplete or unclear.",
                "missing_concepts": ["Unable to determine"]
            }
    except Exception as e:
        st.error(f"Error calling Gemini API: {str(e)}")
        return {
            "score": 0,
            "feedback": f"Error during evaluation: {str(e)}",
            "missing_concepts": ["Error occurred"]
        }

# File processing functions
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        return ""

def extract_text_from_docx(docx_file):
    try:
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Error processing DOCX: {e}")
        return ""

def extract_skills(text):
    if not text:
        return {}
    
    text = text.lower()
    identified_skills = {}
    
    for category, skill_list in COMMON_SKILLS.items():
        found_skills = []
        for skill in skill_list:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text):
                found_skills.append(skill)
        if found_skills:
            identified_skills[category] = found_skills
    
    return identified_skills

def generate_technical_questions(skills, max_questions=7):
    all_possible_questions = []
    
    all_skills = []
    for category, skill_list in skills.items():
        all_skills.extend(skill_list)
    
    skill_frequency = {}
    for skill in all_skills:
        skill_frequency[skill] = skill_frequency.get(skill, 0) + 1
    
    sorted_skills = sorted(skill_frequency.keys(), key=lambda x: skill_frequency[x], reverse=True)
    
    for skill in sorted_skills:
        if skill in TECHNICAL_QUESTIONS:
            all_possible_questions.extend(TECHNICAL_QUESTIONS[skill])
    
    if len(all_possible_questions) < max_questions:
        random.shuffle(GENERIC_QUESTIONS)
        all_possible_questions.extend(GENERIC_QUESTIONS)
    
    unique_questions = []
    question_texts = set()
    
    for q in all_possible_questions:
        if q["question"] not in question_texts:
            unique_questions.append(q)
            question_texts.add(q["question"])
            if len(unique_questions) >= max_questions:
                break
    
    if len(unique_questions) < max_questions:
        for q in GENERIC_QUESTIONS:
            if q["question"] not in question_texts:
                unique_questions.append(q)
                question_texts.add(q["question"])
                if len(unique_questions) >= max_questions:
                    break
    
    return unique_questions[:max_questions]

def get_download_link(text, filename, label="Download"):
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{label}</a>'
    return href

def get_feedback_message(score):
    if score >= 80:
        return random.choice(EVALUATION_POSITIVE)
    elif score >= 60:
        return random.choice(EVALUATION_AVERAGE)
    else:
        return random.choice(EVALUATION_NEEDS_IMPROVEMENT)

def format_skills_message(skills):
    message = ""
    for category, skill_list in skills.items():
        message += f"**{category.capitalize()}**: {', '.join(skill_list)}\n"
    return message

def export_results_as_pdf(candidate_name, interview_date, avg_score, rating, skills, evaluations, questions):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Technical Interview Results", ln=True, align="C")
    pdf.ln(5)
    
    # Candidate info
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Candidate: {candidate_name}", ln=True)
    pdf.cell(0, 10, f"Date: {interview_date}", ln=True)
    pdf.ln(5)
    
    # Summary
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Summary", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Overall Score: {avg_score:.1f}/100", ln=True)
    pdf.cell(0, 10, f"Rating: {rating}", ln=True)
    pdf.ln(5)
    
    # Skills
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Skills", ln=True)
    pdf.set_font("Arial", "", 12)
    for category, skill_list in skills.items():
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, f"{category.capitalize()}", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, ", ".join(skill_list))
    pdf.ln(5)
    
    # Questions and Answers
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Interview Questions and Evaluations", ln=True)
    
    for i, q in enumerate(questions):
        if q['question'] in evaluations:
            data = evaluations[q['question']]
            evaluation = data["evaluation"]
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Question {i+1}: {q['question']}", ln=True)
            
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, f"Answer: {data['answer']}")
            
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Score: {evaluation.get('score', 'N/A')}/100", ln=True)
            
            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, f"Feedback: {evaluation.get('feedback', 'No feedback available')}")
            
            missing = evaluation.get('missing_concepts', [])
            if missing:
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, "Missing concepts:", ln=True)
                pdf.set_font("Arial", "", 12)
                for concept in missing:
                    pdf.cell(0, 10, f"- {concept}", ln=True)
            
            pdf.ln(5)
    
    output_path = "interview_results.pdf"
    pdf.output(output_path)
    return output_path

def generate_interview_summary(candidate_name, interview_date, avg_score, rating, skills, evaluations, questions):
    summary = []
    
    summary.append(f"# Technical Interview Results for {candidate_name}")
    summary.append(f"**Date:** {interview_date}")
    summary.append(f"**Overall Score:** {avg_score:.1f}/100")
    summary.append(f"**Rating:** {rating}")
    summary.append("\n## Skills Profile")
    
    for category, skill_list in skills.items():
        summary.append(f"**{category.capitalize()}:** {', '.join(skill_list)}")
    
    summary.append("\n## Question Analysis")
    
    for i, q in enumerate(questions):
        if q['question'] in evaluations:
            data = evaluations[q['question']]
            evaluation = data["evaluation"]
            score = evaluation.get('score', 0)
            
            summary.append(f"### Question {i+1}: {q['question']}")
            summary.append(f"**Score:** {score}/100")
            summary.append(f"**Feedback:** {evaluation.get('feedback', 'No feedback available')}")
            
            missing = evaluation.get('missing_concepts', [])
            if missing:
                summary.append("**Areas for improvement:**")
                for concept in missing:
                    summary.append(f"- {concept}")
            summary.append("")
    
    summary.append("## Interview Recommendation")
    if avg_score >= 85:
        summary.append("Based on your technical interview performance, you demonstrate strong technical knowledge and communication skills. You're ready to apply for senior positions in your area of expertise.")
    elif avg_score >= 70:
        summary.append("Your technical skills are solid, with some areas that could benefit from deeper understanding. You're well-prepared for mid-level positions.")
    elif avg_score >= 50:
        summary.append("You have a good foundation of technical knowledge, but should continue to build your expertise in key areas. Focus on the concepts mentioned as missing in your feedback.")
    else:
        summary.append("Consider spending more time studying the fundamentals of your technical areas. Focus particularly on the missing concepts highlighted in each question's feedback.")
    
    return "\n".join(summary)

# Streamlit App
st.set_page_config(page_title="Technical Interview Chatbot", layout="wide")

# Initialize session state for chatbot
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "skills" not in st.session_state:
    st.session_state.skills = {}
if "questions" not in st.session_state:
    st.session_state.questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False
if "interview_date" not in st.session_state:
    st.session_state.interview_date = datetime.now().strftime("%Y-%m-%d %H:%M")
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": random.choice(WELCOME_MESSAGES) + " " + random.choice(RESUME_PROMPTS)}]
if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = ""
if "bot_state" not in st.session_state:
    st.session_state.bot_state = "wait_for_resume"
if "max_questions" not in st.session_state:
    st.session_state.max_questions = 5

# Function to add message to chat
def add_message(role, content):
    st.session_state.chat_messages.append({"role": role, "content": content})

# Sidebar for configuration and progress
with st.sidebar:
    st.header("Interview Bot Settings")
    
    if st.session_state.bot_state == "wait_for_resume" or st.session_state.bot_state == "analyzing_resume":
        st.info("Please upload your resume or paste its content in the chat to begin.")
    elif st.session_state.bot_state == "interview":
        # Show progress
        st.subheader("Interview Progress")
        progress = st.session_state.current_question_index / len(st.session_state.questions)
        st.progress(progress)
        st.write(f"Question {st.session_state.current_question_index}/{len(st.session_state.questions)}")
        
        # Show skill focus
        if st.session_state.skills:
            st.subheader("Your Skills Focus")
            for category, skills in st.session_state.skills.items():
                with st.expander(category.capitalize()):
                    st.write(", ".join(skills))
    elif st.session_state.bot_state == "complete":
        st.success("Interview Complete!")
        
        # Show overall score
        evaluations = st.session_state.evaluations
        total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
        avg_score = total_score / len(evaluations) if evaluations else 0
        rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
        
        st.metric("Overall Score", f"{avg_score:.1f}/100")
        st.metric("Rating", rating)
    
    # API configuration
    with st.expander("API Configuration"):
        api_key = st.text_input("Gemini API Key", 
                              value=os.environ.get("GEMINI_API_KEY", ""), 
                              type="password")
        if st.button("Save API Key"):
            os.environ["GEMINI_API_KEY"] = api_key
            st.success("API Key saved for this session")
    
    # Question limit setting
    max_q = st.slider("Number of Questions", min_value=3, max_value=10, value=st.session_state.max_questions)
    if max_q != st.session_state.max_questions:
        st.session_state.max_questions = max_q
    
    # Reset button
    if st.button("Start New Interview"):
        st.session_state.resume_text = ""
        st.session_state.skills = {}
        st.session_state.questions = []
        st.session_state.current_question_index = 0
        st.session_state.evaluations = {}
        st.session_state.interview_complete = False
        st.session_state.bot_state = "wait_for_resume"
        st.session_state.chat_messages = [{"role": "assistant", "content": random.choice(WELCOME_MESSAGES) + " " + random.choice(RESUME_PROMPTS)}]
        st.session_state.candidate_name = ""
        st.rerun()

# Main chat area
st.title("Technical Interview Chatbot 🤖")

# Display chat messages
for message in st.session_state.chat_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input based on the current state
def process_user_input(user_input):
    add_message("user", user_input)
    
    # State: Waiting for resume
    if st.session_state.bot_state == "wait_for_resume":
        # Check if this is a name
        if len(user_input.split()) <= 3 and len(st.session_state.chat_messages) <= 3:
            st.session_state.candidate_name = user_input
            add_message("assistant", f"Nice to meet you, {user_input}! Please upload your resume or paste its content so I can prepare relevant technical questions.")
            return
        
        # Treat as resume text
        st.session_state.resume_text = user_input
        st.session_state.bot_state = "analyzing_resume"
        add_message("assistant", "Thanks for sharing your resume! I'm analyzing it to identify your technical skills...")
        
        # Extract skills
        skills = extract_skills(user_input)
        if not skills:
            add_message("assistant", "I couldn't identify specific technical skills from your resume. Let's add some manually. What are your top technical skills? (e.g., Python, Java, AWS)")
            st.session_state.bot_state = "manual_skills"
        else:
            st.session_state.skills = skills
            skill_message = random.choice(SKILL_MESSAGES) + "\n\n" + format_skills_message(skills)
            skill_message += "\n\nAre these skills accurate? You can add more skills if needed, or type 'start interview' when you're ready."
            add_message("assistant", skill_message)
            st.session_state.bot_state = "confirm_skills"
    
    # State: Manual skills entry
    elif st.session_state.bot_state == "manual_skills":
        skills_input = user_input.lower()
        manual_skills = {}
        
        for category, skill_list in COMMON_SKILLS.items():
            found_skills = []
            for skill in skill_list:
                if skill in skills_input:
                    found_skills.append(skill)
            if found_skills:
                manual_skills[category] = found_skills
        
        if not manual_skills:
            # If no matching skills, add generic programming skills
            manual_skills['programming'] = ['python', 'java']
            manual_skills['tools'] = ['git']
        
        st.session_state.skills = manual_skills
        skill_message = "Thanks! I've added these skills to your profile:\n\n" + format_skills_message(manual_skills)
        skill_message += "\n\nReady to start the interview? Type 'start interview' when you're ready."
        add_message("assistant", skill_message)
        st.session_state.bot_state = "confirm_skills"
    
    # State: Confirming skills
    elif st.session_state.bot_state == "confirm_skills":
        if "start interview" in user_input.lower() or "ready" in user_input.lower() or "yes" in user_input.lower():
            # Generate technical questions
            technical_questions = generate_technical_questions(st.session_state.skills, st.session_state.max_questions)
            st.session_state.questions = technical_questions
            st.session_state.current_question_index = 0
            
            # Start interview
            start_message = random.choice(INTERVIEW_START_MESSAGES)
            first_question = technical_questions[0]["question"] if technical_questions else "Tell me about your background in technology."
            add_message("assistant", f"{start_message}\n\n**Question 1:** {first_question}")
            st.session_state.bot_state = "interview"
        else:
            # Handle adding more skills
            new_skills = extract_skills(user_input)
            if new_skills:
                for category, skills_list in new_skills.items():
                    if category in st.session_state.skills:
                        for skill in skills_list:
                            if skill not in st.session_state.skills[category]:
                                st.session_state.skills[category].append(skill)
                    else:
                        st.session_state.skills[category] = skills_list
                
                add_message("assistant", f"I've updated your skills profile. Type 'start interview' when you're ready to begin.")
            else:
                add_message("assistant", "I'm ready whenever you are. Type 'start interview' to begin.")
    
    # State: Conducting interview
    elif st.session_state.bot_state == "interview":
        current_index = st.session_state.current_question_index
        current_question = st.session_state.questions[current_index]
        
        # Evaluate the answer
        evaluation = validate_answer_with_gemini(
            question=current_question['question'],
            answer=user_input,
            expected_keywords=current_question['expected_keywords']
        )
        
        # Store evaluation
        st.session_state.evaluations[current_question['question']] = {
            "answer": user_input,
            "evaluation": evaluation
        }
        
# Provide feedback
        score = evaluation.get('score', 0)
        feedback_message = get_feedback_message(score)
        feedback = f"{feedback_message}\n\n**Score:** {score}/100\n\n{evaluation.get('feedback', '')}"
        
        missing = evaluation.get('missing_concepts', [])
        if missing:
            feedback += "\n\n**Areas to improve:**\n"
            for concept in missing:
                feedback += f"- {concept}\n"
        
        add_message("assistant", feedback)
        
        # Move to next question or end interview
        current_index += 1
        st.session_state.current_question_index = current_index
        
        if current_index < len(st.session_state.questions):
            next_question = st.session_state.questions[current_index]["question"]
            transition = random.choice(QUESTION_TRANSITIONS)
            add_message("assistant", f"{transition}\n\n**Question {current_index + 1}:** {next_question}")
        else:
            # Interview complete
            st.session_state.bot_state = "complete"
            st.session_state.interview_complete = True
            
            # Calculate overall score
            evaluations = st.session_state.evaluations
            total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
            avg_score = total_score / len(evaluations) if evaluations else 0
            rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
            
            # Generate summary
            summary = f"""
            ## Interview Complete!
            
            Thank you for completing the technical interview practice session. Here's your performance summary:
            
            **Overall Score:** {avg_score:.1f}/100
            **Rating:** {rating}
            
            Would you like to:
            1. Review your answers and feedback
            2. Export your results as PDF
            3. Generate a detailed interview summary
            4. Start a new interview
            
            Just let me know what you'd like to do next!
            """
            add_message("assistant", summary)
    
    # State: Interview complete - handle post-interview options
    elif st.session_state.bot_state == "complete":
        if "review" in user_input.lower() or "answers" in user_input.lower():
            # Review answers and feedback
            review = "## Your Interview Responses and Feedback\n\n"
            
            for i, q in enumerate(st.session_state.questions):
                if q['question'] in st.session_state.evaluations:
                    data = st.session_state.evaluations[q['question']]
                    evaluation = data["evaluation"]
                    
                    review += f"### Question {i+1}: {q['question']}\n"
                    review += f"**Your answer:** {data['answer']}\n\n"
                    review += f"**Score:** {evaluation.get('score', 0)}/100\n"
                    review += f"**Feedback:** {evaluation.get('feedback', 'No feedback available')}\n\n"
                    
                    missing = evaluation.get('missing_concepts', [])
                    if missing:
                        review += "**Areas for improvement:**\n"
                        for concept in missing:
                            review += f"- {concept}\n"
                    review += "\n---\n\n"
            
            add_message("assistant", review)
            
        elif "pdf" in user_input.lower() or "export" in user_input.lower():
            # Generate PDF
            try:
                evaluations = st.session_state.evaluations
                total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
                avg_score = total_score / len(evaluations) if evaluations else 0
                rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
                
                pdf_path = export_results_as_pdf(
                    st.session_state.candidate_name or "Candidate",
                    st.session_state.interview_date,
                    avg_score,
                    rating,
                    st.session_state.skills,
                    st.session_state.evaluations,
                    st.session_state.questions
                )
                
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                pdf_link = f'<a href="data:application/pdf;base64,{pdf_b64}" download="interview_results.pdf">Download Interview Results (PDF)</a>'
                
                add_message("assistant", f"Your interview results are ready! {pdf_link}")
            except Exception as e:
                add_message("assistant", f"Sorry, there was an error generating the PDF: {str(e)}")
        
        elif "summary" in user_input.lower() or "detailed" in user_input.lower():
            # Generate detailed summary
            evaluations = st.session_state.evaluations
            total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
            avg_score = total_score / len(evaluations) if evaluations else 0
            rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
            
            summary = generate_interview_summary(
                st.session_state.candidate_name or "Candidate",
                st.session_state.interview_date,
                avg_score,
                rating,
                st.session_state.skills,
                st.session_state.evaluations,
                st.session_state.questions
            )
            
            add_message("assistant", summary)
            
            summary_text = summary.encode()
            summary_b64 = base64.b64encode(summary_text).decode()
            summary_link = f'<a href="data:text/markdown;base64,{summary_b64}" download="interview_summary.md">Download Summary (Markdown)</a>'
            
            add_message("assistant", f"You can also download this summary: {summary_link}")
        
        elif "new" in user_input.lower() or "start" in user_input.lower() or "again" in user_input.lower():
            # Reset for new interview
            st.session_state.resume_text = ""
            st.session_state.skills = {}
            st.session_state.questions = []
            st.session_state.current_question_index = 0
            st.session_state.evaluations = {}
            st.session_state.interview_complete = False
            st.session_state.bot_state = "wait_for_resume"
            st.session_state.chat_messages = [{"role": "assistant", "content": random.choice(WELCOME_MESSAGES) + " " + random.choice(RESUME_PROMPTS)}]
            st.rerun()
        else:
            add_message("assistant", """
            What would you like to do next?
            
            1. **Review your answers and feedback**
            2. **Export your results as PDF**
            3. **Generate a detailed interview summary**
            4. **Start a new interview**
            
            Just let me know what option you prefer.
            """)

# File uploader for resume
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"], key="resume_upload")

if uploaded_file is not None and not st.session_state.resume_text:
    # Process uploaded file
    file_extension = uploaded_file.name.split(".")[-1].lower()
    
    if file_extension == "pdf":
        resume_text = extract_text_from_pdf(uploaded_file)
    elif file_extension == "docx":
        resume_text = extract_text_from_docx(uploaded_file)
    else:
        resume_text = ""
        st.error("Unsupported file format. Please upload a PDF or DOCX file.")
    
    if resume_text:
        st.session_state.resume_text = resume_text
        st.session_state.bot_state = "analyzing_resume"
        add_message("assistant", "Thanks for uploading your resume! I'm analyzing it to identify your technical skills...")
        
        # Extract skills
        skills = extract_skills(resume_text)
        if not skills:
            add_message("assistant", "I couldn't identify specific technical skills from your resume. Let's add some manually. What are your top technical skills? (e.g., Python, Java, AWS)")
            st.session_state.bot_state = "manual_skills"
        else:
            st.session_state.skills = skills
            skill_message = random.choice(SKILL_MESSAGES) + "\n\n" + format_skills_message(skills)
            skill_message += "\n\nAre these skills accurate? You can add more skills if needed, or type 'start interview' when you're ready."
            add_message("assistant", skill_message)
            st.session_state.bot_state = "confirm_skills"
        
        st.rerun()

# Chat input
if user_input := st.chat_input("Type here"):
    process_user_input(user_input)
    st.rerun()

# Add download links for interview summary when interview is complete
if st.session_state.interview_complete:
    with st.sidebar:
        st.subheader("Export Results")
        
        # Calculate score
        evaluations = st.session_state.evaluations
        total_score = sum(data["evaluation"].get("score", 0) for data in evaluations.values())
        avg_score = total_score / len(evaluations) if evaluations else 0
        rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
        
        # Generate summary
        summary = generate_interview_summary(
            st.session_state.candidate_name or "Candidate",
            st.session_state.interview_date,
            avg_score,
            rating,
            st.session_state.skills,
            st.session_state.evaluations,
            st.session_state.questions
        )
        
        # Create download links
        st.markdown(get_download_link(summary, "interview_summary.md", "Download Summary (Markdown)"), unsafe_allow_html=True)
        
        # Export PDF link - handled in chat to avoid duplicate files
        if st.button("Generate PDF"):
            try:
                pdf_path = export_results_as_pdf(
                    st.session_state.candidate_name or "Candidate",
                    st.session_state.interview_date,
                    avg_score,
                    rating,
                    st.session_state.skills,
                    st.session_state.evaluations,
                    st.session_state.questions
                )
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                pdf_b64 = base64.b64encode(pdf_bytes).decode()
                st.markdown(f'<a href="data:application/pdf;base64,{pdf_b64}" download="interview_results.pdf">Download Interview Results (PDF)</a>', unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")

# Footer
st.markdown("---")
st.markdown("Technical Interview Chatbot | Powered by Streamlit and Gemini", unsafe_allow_html=True)
