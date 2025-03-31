import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import PyPDF2
import docx
import streamlit as st

# Ensure necessary NLTK resources are available
nltk.download('punkt')
nltk.download('stopwords')

# List of common skills to look for in resumes
COMMON_SKILLS = {
    'programming': ['python', 'java', 'javascript', 'html', 'css', 'c++', 'c#', 'ruby', 'php', 'typescript', 'sql', 'r', 'perl', 'swift', 'kotlin', 'scala', 'go', 'rust'],
    'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express', '.net', 'laravel', 'ruby on rails', 'tensorflow', 'pytorch'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'cassandra', 'redis', 'elasticsearch', 'dynamodb'],
    'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'cloud computing', 'docker', 'kubernetes', 'serverless'],
    'tools': ['git', 'github', 'bitbucket', 'jira', 'confluence', 'jenkins', 'travis ci', 'circle ci', 'agile', 'scrum', 'kanban', 'figma', 'sketch'],
    'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking', 'creativity', 'time management', 'project management'],
}

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file, handling empty pages."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text if text else "Could not extract text from PDF."

def extract_text_from_docx(docx_file):
    """Extract text from a DOCX file."""
    doc = docx.Document(docx_file)
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

def extract_skills(text):
    """Extract skills from text based on predefined skill lists."""
    text = text.lower()
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [w for w in tokens if w.isalnum() and w not in stop_words]
    
    identified_skills = {}
    for category, skill_list in COMMON_SKILLS.items():
        found_skills = [skill for skill in skill_list if skill in text]
        if found_skills:
            identified_skills[category] = found_skills
    
    return identified_skills

def generate_questions(skills):
    """Generate questions based on identified skills."""
    questions = [
        "Could you tell me more about your experience?",
        "What are you looking for in your next role?"
    ]
    for category, skill_list in skills.items():
        if category == 'programming':
            questions.append(f"Which programming language are you most proficient in: {', '.join(skill_list[:3])}?")
        if category == 'frameworks':
            questions.append(f"Can you describe a project where you used {skill_list[0]}?")
        if category == 'databases':
            questions.append(f"How experienced are you with {', '.join(skill_list)}?")
        if category == 'cloud':
            questions.append(f"Have you worked with {skill_list[0]} in production?")
        if category == 'soft_skills':
            questions.append("Can you give an example of demonstrating leadership?")
    return questions

# Streamlit App
st.title("Resume Processing Chatbot")

st.header("Step 1: Upload Resume")
uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    st.success("File successfully uploaded!")
    if uploaded_file.name.endswith('.pdf'):
        resume_text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith('.docx'):
        resume_text = extract_text_from_docx(uploaded_file)
    else:
        resume_text = uploaded_file.read().decode(errors="replace")
    
    st.header("Step 2: Extracted Skills")
    skills = extract_skills(resume_text)
    if skills:
        for category, skill_list in skills.items():
            st.subheader(category.capitalize())
            st.write(", ".join(skill_list))
    else:
        st.warning("No specific skills were identified. Please check the resume format.")
    
    st.header("Step 3: Interview Questions")
    questions = generate_questions(skills)
    for i, question in enumerate(questions, 1):
        st.write(f"{i}. {question}")
    
    st.header("Chat Interface")
    st.info("Use the questions above to interview the candidate.")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Ask a question:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("assistant"):
            response = f"Please provide your answer to: {prompt}"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
