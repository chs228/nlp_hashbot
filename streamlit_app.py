import re
import streamlit as st
import io
import base64
import json
import requests
import os
import random
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import markdown
import pdfkit
from smail import export_results_to_email
# For PDF and DOCX processing
try:
    import PyPDF2
except ImportError:
    st.error("PyPDF2 is not installed. Please install it with: pip install PyPDF2")

try:
    import docx
except ImportError:
    st.error("python-docx is not installed. Please install it with: pip install python-docx")


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

# Gemini API functions
def validate_answer_with_gemini(question, answer, expected_keywords):
    """
    Use Google's Gemini API to validate a candidate's answer.
    """
    # Replace with your Gemini API key or use from environment variables
    api_key = os.environ.get("GEMINI_API_KEY", st.secrets.get("AIzaSyCx70_PG_V6tkCsarNnIP9qs_fl5THZIMI", ""))
    
    if not api_key:
        st.warning("Gemini API key not found. Validation will be simulated.")
        # Simulate validation
        keyword_count = sum(1 for keyword in expected_keywords if keyword.lower() in answer.lower())
        score = min(keyword_count / len(expected_keywords), 1.0) * 100
        return {
            "score": score,
            "feedback": "This is simulated feedback. Please configure Gemini API for actual validation.",
            "missing_concepts": [k for k in expected_keywords if k.lower() not in answer.lower()]
        }
    
    # Gemini API endpoint
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    # Construct the prompt for Gemini
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
    
    # Make API request
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
        
        # Parse Gemini's response
        response_data = response.json()
        generated_text = response_data["candidates"][0]["content"]["parts"][0]["text"]
        
        # Extract JSON from the response
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
        
        try:
            # Clean the JSON string - remove markdown code block markers if present
            json_str = json_str.replace("```json", "").replace("```", "").strip()
            
            # Try to parse the JSON
            result = json.loads(json_str)
            
            # Ensure all required fields are present
            if "score" not in result:
                result["score"] = 50  # Default score
            if "feedback" not in result:
                result["feedback"] = "No specific feedback provided."
            if "missing_concepts" not in result:
                result["missing_concepts"] = []
                
            return result
            
        except json.JSONDecodeError:
            # If we can't parse JSON, create a default response
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
    """Extract text from a PDF file using a more robust approach."""
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
    """Extract text from a DOCX file with error handling."""
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
    """Extract skills from text based on predefined skill lists."""
    if not text:
        return {}
    
    text = text.lower()
    identified_skills = {}
    
    for category, skill_list in COMMON_SKILLS.items():
        found_skills = []
        
        for skill in skill_list:
            # Simple pattern matching - find the skill as a whole word
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text):
                found_skills.append(skill)
                
        if found_skills:
            identified_skills[category] = found_skills
    
    return identified_skills

def generate_technical_questions(skills, max_questions=7):
    """Generate specific technical questions based on identified skills, limited to max_questions."""
    all_possible_questions = []
    
    # Flatten the skills into a list
    all_skills = []
    for category, skill_list in skills.items():
        all_skills.extend(skill_list)
    
    # Prioritize the most important skills by sorting frequency
    skill_frequency = {}
    for skill in all_skills:
        if skill in skill_frequency:
            skill_frequency[skill] += 1
        else:
            skill_frequency[skill] = 1
    
    # Sort skills by frequency (most frequent first)
    sorted_skills = sorted(skill_frequency.keys(), key=lambda x: skill_frequency[x], reverse=True)
    
    # Get technical questions for each skill
    for skill in sorted_skills:
        if skill in TECHNICAL_QUESTIONS:
            all_possible_questions.extend(TECHNICAL_QUESTIONS[skill])
    
    # If we have too few questions, add generic questions
    if len(all_possible_questions) < max_questions:
        random.shuffle(GENERIC_QUESTIONS)
        all_possible_questions.extend(GENERIC_QUESTIONS)
    
    # Ensure uniqueness by question text
    unique_questions = []
    question_texts = set()
    
    for q in all_possible_questions:
        if q["question"] not in question_texts:
            unique_questions.append(q)
            question_texts.add(q["question"])
            if len(unique_questions) >= max_questions:
                break
    
    # If we still don't have enough questions, add generic ones
    if len(unique_questions) < max_questions:
        for q in GENERIC_QUESTIONS:
            if q["question"] not in question_texts:
                unique_questions.append(q)
                question_texts.add(q["question"])
                if len(unique_questions) >= max_questions:
                    break
    
    # Limit to max_questions
    return unique_questions[:max_questions]

def get_download_link(text, filename, label="Download processed text"):
    """Generate a download link for text file."""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{label}</a>'
    return href

# Streamlit App
st.set_page_config(page_title="Technical Interview Bot", layout="wide")
st.title("Technical Interview Bot")
st.subheader("Resume Analysis & Question Generation with AI Validation")

# Initialize session state
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "skills" not in st.session_state:
    st.session_state.skills = {}
if "questions" not in st.session_state:
    st.session_state.questions = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_step" not in st.session_state:
    st.session_state.current_step = 1
if "evaluations" not in st.session_state:
    st.session_state.evaluations = {}
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "interview_date" not in st.session_state:
    st.session_state.interview_date = datetime.now().strftime("%Y-%m-%d %H:%M")
if "max_questions" not in st.session_state:
    st.session_state.max_questions = 7
    
# Create sidebar for the workflow steps
with st.sidebar:
    st.header("Workflow")
    st.write("1. Upload Resume")
    st.write("2. Extract Skills")
    st.write("3. Technical Interview")
    
    st.divider()
    
    if st.session_state.current_step > 1:
        if st.button("Start Over"):
            st.session_state.resume_text = ""
            st.session_state.skills = {}
            st.session_state.questions = []
            st.session_state.messages = []
            st.session_state.current_step = 1
            st.session_state.evaluations = {}
            st.session_state.current_question = None
            st.session_state.interview_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.rerun()
    
    # Gemini API configuration
    with st.expander("Gemini API Configuration"):
        api_key = st.text_input("Gemini API Key", 
                               value=os.environ.get("GEMINI_API_KEY", ""), 
                               type="password")
        if st.button("Save API Key"):
            os.environ["GEMINI_API_KEY"] = api_key
            st.success("API Key saved for this session")
    
    # Display progress if in interview step
    if st.session_state.current_step == 3 and st.session_state.questions:
        st.subheader("Interview Progress")
        completed = len(st.session_state.evaluations)
        total = len(st.session_state.questions)
        st.progress(completed / total)
        st.write(f"Questions answered: {completed}/{total}")

# Step 1: Upload Resume
if st.session_state.current_step == 1:
    st.header("Step 1: Upload Resume")
    uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx", "txt"])
    
    # Alternative direct text input
    text_input = st.text_area("Or paste resume text directly:", height=200)
    
    process_button = st.button("Process Resume")
    
    if process_button:
        if uploaded_file is not None:
            # Extract text based on file type
            if uploaded_file.name.endswith('.pdf'):
                resume_text = extract_text_from_pdf(uploaded_file)
            elif uploaded_file.name.endswith('.docx'):
                resume_text = extract_text_from_docx(uploaded_file)
            else:  # Assume it's a text file
                resume_text = uploaded_file.getvalue().decode("utf-8", errors="replace")
            
            st.session_state.resume_text = resume_text
            st.session_state.current_step = 2
            st.rerun()
            
        elif text_input:
            st.session_state.resume_text = text_input
            st.session_state.current_step = 2
            st.rerun()
            
        else:
            st.error("Please upload a file or paste text to continue.")

# Step 2: Extract Skills
elif st.session_state.current_step == 2:
    st.header("Step 2: Extract Skills")
    
    # Display a snippet of the resume
    with st.expander("Resume Text Preview"):
        st.text_area("Resume content:", 
                    value=st.session_state.resume_text[:500] + "..." if len(st.session_state.resume_text) > 500 else st.session_state.resume_text,
                    height=150,
                    disabled=True)
    
    # Extract skills
    skills = extract_skills(st.session_state.resume_text)
    st.session_state.skills = skills
    
    # Display extracted skills
    if skills:
        st.subheader("Identified Skills")
        for category, skill_list in skills.items():
            with st.expander(f"{category.capitalize()} ({len(skill_list)} skills)"):
                st.write(", ".join(skill_list))
    else:
        st.warning("No specific skills were identified. Please add skills manually.")
    
    # Manual skill entry
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Add Additional Skills")
        new_skill = st.text_input("Enter a skill that's missing:")
        skill_category = st.selectbox("Category:", list(COMMON_SKILLS.keys()))
        
        if st.button("Add Skill") and new_skill:
            if skill_category in st.session_state.skills:
                if new_skill not in st.session_state.skills[skill_category]:
                    st.session_state.skills[skill_category].append(new_skill)
            else:
                st.session_state.skills[skill_category] = [new_skill]
            st.rerun()
    
    with col2:
        st.subheader("Interview Settings")
        st.info(f"Maximum {st.session_state.max_questions} questions will be generated")
        
        st.markdown("""
        The system will generate the most relevant technical questions based on the identified skills.
        Focus will be given to the most prominent skills in the resume.
        """)
    
    if st.button("Start Technical Interview"):
        # Generate specific technical questions based on skills (max 7)
        technical_questions = generate_technical_questions(st.session_state.skills, st.session_state.max_questions)
        st.session_state.questions = technical_questions
        
        if technical_questions:
            st.session_state.current_question = technical_questions[0]
        
        st.session_state.current_step = 3
        st.rerun()

# Step 3: Technical Interview
elif st.session_state.current_step == 3:
    st.header("Step 3: Technical Interview")
    
    # Show all questions in the sidebar
    with st.sidebar:
        st.subheader("All Technical Questions")
        for i, q in enumerate(st.session_state.questions):
            q_status = "✅" if q['question'] in st.session_state.evaluations else "⬜"
            if st.button(f"{q_status} Q{i+1}: {q['question'][:25]}...", key=f"q_{i}"):
                st.session_state.current_question = q
                st.rerun()
    
    # Main interview area
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Current Question")
        
        if st.session_state.current_question:
            current_q = st.session_state.current_question
            q_index = st.session_state.questions.index(current_q) + 1
            st.write(f"**Question {q_index} of {len(st.session_state.questions)}:**")
            st.write(f"**{current_q['question']}**")
            
            # Check if this question has already been answered
            already_answered = current_q['question'] in st.session_state.evaluations
            if already_answered:
                st.info("You have already answered this question. Your previous answer:")
                st.text_area("Previous answer:", 
                           value=st.session_state.evaluations[current_q['question']]['answer'],
                           height=150,
                           disabled=True)
                
                if st.button("Edit Answer"):
                    # Remove previous evaluation to allow re-answering
                    del st.session_state.evaluations[current_q['question']]
                    st.rerun()
            else:
                # Input area for answer
                answer = st.text_area("Your answer:", height=200)
                
                if st.button("Submit Answer for Evaluation"):
                    if answer:
                        # Validate with Gemini
                        evaluation = validate_answer_with_gemini(
                            question=current_q['question'],
                            answer=answer,
                            expected_keywords=current_q['expected_keywords']
                        )
                        
                        # Save the evaluation
                        q_key = current_q['question']
                        st.session_state.evaluations[q_key] = {
                            "answer": answer,
                            "evaluation": evaluation
                        }
                        
                        # Move to next question if available
                        current_index = st.session_state.questions.index(current_q)
                        if current_index < len(st.session_state.questions) - 1:
                            st.session_state.current_question = st.session_state.questions[current_index + 1]
                        
                        st.rerun()
                    else:
                        st.error("Please provide an answer before submitting.")
        else:
            st.info("No questions available. Please return to the skills extraction step.")
    
    with col2:
        st.subheader("Evaluation Results")
        
        if st.session_state.evaluations:
            # Create a list of evaluations sorted by question order
            sorted_evaluations = []
            for q in st.session_state.questions:
                if q['question'] in st.session_state.evaluations:
                    sorted_evaluations.append((q['question'], st.session_state.evaluations[q['question']]))
            
            # Display evaluations
            for q, data in sorted_evaluations:
                q_index = next((i+1 for i, question in enumerate(st.session_state.questions) if question['question'] == q), "")
                with st.expander(f"Q{q_index}: {q[:40]}..."):
                    evaluation = data["evaluation"]
                    score = evaluation.get('score', 0)
                    
                    # Color code score
                    score_color = "#4CAF50" if score >= 80 else "#FFC107" if score >= 60 else "#F44336"
                    
                    st.markdown(f"<h3 style='color:{score_color}'>Score: {score}/100</h3>", unsafe_allow_html=True)
                    st.write(f"**Feedback:** {evaluation.get('feedback', 'No feedback available')}")
                    
                    missing = evaluation.get('missing_concepts', [])
                    if missing:
                        st.write("**Missing concepts:**")
                        for concept in missing:
                            st.write(f"- {concept}")
        else:
            st.info("No evaluations yet. Submit answers to see results.")
    
    # Summary and export
    if st.session_state.evaluations and len(st.session_state.evaluations) == len(st.session_state.questions):
        st.header("Interview Complete! 🎉")
        
        # Calculate overall score
        total_score = sum(data["evaluation"].get("score", 0) for data in st.session_state.evaluations.values())
        avg_score = total_score / len(st.session_state.evaluations)
        
        # Define score rating
        rating = "Excellent" if avg_score >= 85 else "Good" if avg_score >= 70 else "Average" if avg_score >= 50 else "Needs Improvement"
        
        # Display summary
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overall Technical Score", f"{avg_score:.1f}/100")
        with col2:
            st.metric("Rating", rating)
        
        # Export option
        # Export option
        st.markdown("---")
        st.subheader("Export Results")
        
        export_tab1, export_tab2 = st.tabs(["Download", "Email"])
        
        with export_tab1:
            export_format = st.radio("Export Format", ["Markdown", "JSON"])
            
            if st.button("Download Interview Results"):
                if export_format == "Markdown":
                    export_text = "# Technical Interview Results\n\n"
                    export_text += f"Date: {st.session_state.interview_date}\n"
                    export_text += f"Overall Score: {avg_score:.1f}/100\n"
                    export_text += f"Rating: {rating}\n\n"
                    
                    export_text += "## Extracted Skills\n"
                    for category, skill_list in st.session_state.skills.items():
                        export_text += f"### {category.capitalize()}\n"
                        export_text += ", ".join(skill_list) + "\n\n"
                    
                    export_text += "## Interview Questions and Evaluations\n\n"
                    for i, q in enumerate(st.session_state.questions):
                        if q['question'] in st.session_state.evaluations:
                            data = st.session_state.evaluations[q['question']]
                            evaluation = data["evaluation"]
                            export_text += f"### Question {i+1}: {q['question']}\n"
                            export_text += f"**Answer:** {data['answer']}\n\n"
                            export_text += f"**Score:** {evaluation.get('score', 'N/A')}/100\n"
                            export_text += f"**Feedback:** {evaluation.get('feedback', 'No feedback available')}\n"
                            
                            missing = evaluation.get('missing_concepts', [])
                            if missing:
                                export_text += "**Missing concepts:**\n"
                                for concept in missing:
                                    export_text += f"- {concept}\n"
                            export_text += "\n---\n\n"
                    
                    st.markdown(get_download_link(export_text, "interview_results.md", "Download as Markdown"), unsafe_allow_html=True)
                else:
                    # JSON export
                    export_data = {
                        "date": st.session_state.interview_date,
                        "overall_score": avg_score,
                        "rating": rating,
                        "skills": st.session_state.skills,
                        "questions": []
                    }
                    
                    for i, q in enumerate(st.session_state.questions):
                        if q['question'] in st.session_state.evaluations:
                            data = st.session_state.evaluations[q['question']]
                            export_data["questions"].append({
                                "question_number": i+1,
                                "question_text": q['question'],
                                "answer": data['answer'],
                                "score": data['evaluation'].get('score', 0),
                                "feedback": data['evaluation'].get('feedback', ''),
                                "missing_concepts": data['evaluation'].get('missing_concepts', [])
                            })
                    
                    json_str = json.dumps(export_data, indent=2)
                    st.markdown(get_download_link(json_str, "interview_results.json", "Download as JSON"), unsafe_allow_html=True)
        
# Inside the export_tab2 section, replace the existing code with this:
            with export_tab2:
                def generate_interview_results_pdf(interview_data):
                    """Generate a clean PDF with interview results - no markdown involved."""
                    try:
                        # Extract data from the interview_data dictionary
                        date = interview_data.get("date", "Not specified")
                        overall_score = interview_data.get("overall_score", 0)
                        rating = interview_data.get("rating", "Not rated")
                        skills = interview_data.get("skills", {})
                        questions = interview_data.get("questions", [])
                        
                        # Create the content directly in HTML (required for pdfkit)
                        html_content = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                            <meta charset="UTF-8">
                            <title>Technical Interview Results</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 40px; font-size: 12px; }}
                                h1 {{ color: #333366; }}
                                h2 {{ color: #336699; margin-top: 20px; }}
                                .score {{ font-weight: bold; }}
                                hr {{ border: 1px solid #eee; }}
                                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                                th {{ background-color: #f2f2f2; }}
                                .high-score {{ color: green; }}
                                .medium-score {{ color: orange; }}
                                .low-score {{ color: red; }}
                            </style>
                        </head>
                        <body>
                            <h1>Technical Interview Results</h1>
                            <p><strong>Date:</strong> {date}</p>
                            <p><strong>Overall Score:</strong> <span class="score">{overall_score:.1f}/100</span></p>
                            <p><strong>Rating:</strong> {rating}</p>
                            
                            <h2>Extracted Skills</h2>
                        """
                        
                        # Add skills table
                        if skills:
                            html_content += """
                            <table>
                                <tr>
                                    <th>Category</th>
                                    <th>Skills</th>
                                </tr>
                            """
                            
                            for category, skill_list in skills.items():
                                html_content += f"""
                                <tr>
                                    <td>{category.capitalize()}</td>
                                    <td>{", ".join(skill_list)}</td>
                                </tr>
                                """
                            
                            html_content += "</table>"
                        else:
                            html_content += "<p>No skills were identified.</p>"
                        
                        # Add questions and evaluations
                        html_content += "<h2>Interview Questions and Evaluations</h2>"
                        
                        for q in questions:
                            question_text = q.get("question_text", "")
                            question_number = q.get("question_number", "")
                            answer = q.get("answer", "")
                            score = q.get("score", 0)
                            feedback = q.get("feedback", "No feedback available")
                            missing_concepts = q.get("missing_concepts", [])
                            
                            # Determine score class
                            score_class = "high-score" if score >= 80 else "medium-score" if score >= 60 else "low-score"
                            
                            html_content += f"""
                            <div class="question">
                                <h3>Question {question_number}: {question_text}</h3>
                                <p><strong>Answer:</strong> {answer}</p>
                                <p><strong>Score:</strong> <span class="{score_class}">{score}/100</span></p>
                                <p><strong>Feedback:</strong> {feedback}</p>
                            """
                            
                            if missing_concepts:
                                html_content += "<p><strong>Missing concepts:</strong></p><ul>"
                                for concept in missing_concepts:
                                    html_content += f"<li>{concept}</li>"
                                html_content += "</ul>"
                            
                            html_content += "<hr></div>"
                        
                        html_content += """
                        </body>
                        </html>
                        """
                        
                        # Convert HTML to PDF
                        options = {
                            'page-size': 'A4',
                            'encoding': 'UTF-8',
                            'margin-top': '15mm',
                            'margin-right': '15mm',
                            'margin-bottom': '15mm',
                            'margin-left': '15mm'
                        }
                        
                        pdf = pdfkit.from_string(html_content, False, options=options)
                        return pdf
                    
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        return None
                
                # Update the email function for the export tab
                def export_results_to_email():
                    recipient_email = st.text_input("Recipient Email")
                    email_subject = st.text_input("Email Subject", f"Technical Interview Results - {st.session_state.interview_date}")
                    
                    if st.button("Send Results via Email"):
                        if recipient_email:
                            # Prepare all interview data in a dictionary
                            interview_data = {
                                "date": st.session_state.interview_date,
                                "overall_score": avg_score,
                                "rating": rating,
                                "skills": st.session_state.skills,
                                "questions": []
                            }
                            
                            # Add questions and evaluations
                            for i, q in enumerate(st.session_state.questions):
                                if q['question'] in st.session_state.evaluations:
                                    data = st.session_state.evaluations[q['question']]
                                    evaluation = data["evaluation"]
                                    
                                    interview_data["questions"].append({
                                        "question_number": i+1,
                                        "question_text": q['question'],
                                        "answer": data['answer'],
                                        "score": evaluation.get('score', 0),
                                        "feedback": evaluation.get('feedback', ''),
                                        "missing_concepts": evaluation.get('missing_concepts', [])
                                    })
                            
                            # Generate PDF directly (no markdown)
                            pdf_data = generate_interview_results_pdf(interview_data)
                            
                            if pdf_data:
                                # Simple email body
                                email_body = f"""
                Technical Interview Results Summary
                
                Date: {st.session_state.interview_date}
                Overall Score: {avg_score:.1f}/100
                Rating: {rating}
                
                The complete interview results are attached as a PDF.
                """
                                
                                # Send email with PDF attachment
                                success, message = send_email(
                                    recipient_email, 
                                    email_subject, 
                                    email_body,
                                    pdf_data,
                                    "interview_results.pdf"
                                )
                                
                                if success:
                                    st.success(message)
                                else:
                                    st.error(message)
                            else:
                                st.error("Failed to generate PDF. Please check that wkhtmltopdf is installed.")
                        else:
                            st.error("Please enter a recipient email address")
