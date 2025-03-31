import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import PyPDF2
import docx
import streamlit as st

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    
try:
    nltk.data.find('corpora/stopwords')
except LookupError:
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
    """Extract text from a PDF file."""
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(docx_file):
    """Extract text from a DOCX file."""
    doc = docx.Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def extract_skills(text):
    """Extract skills from text based on predefined skill lists."""
    text = text.lower()
    
    # Tokenize the text
    tokens = word_tokenize(text)
    
    # Remove stop words
    stop_words = set(stopwords.words('english'))
    filtered_tokens = [w for w in tokens if w.isalnum() and w not in stop_words]
    
    # Extract skills
    identified_skills = {}
    
    for category, skill_list in COMMON_SKILLS.items():
        found_skills = []
        
        # Single word skills
        for skill in skill_list:
            if " " not in skill and skill in filtered_tokens:
                found_skills.append(skill)
            # Multi-word skills
            elif " " in skill and skill in text:
                found_skills.append(skill)
                
        if found_skills:
            identified_skills[category] = found_skills
    
    return identified_skills

def generate_questions(skills):
    """Generate questions based on identified skills."""
    questions = []
    
    # General questions
    questions.append("Could you tell me more about your experience?")
    questions.append("What are you looking for in your next role?")
    
    # Skill-specific questions
    for category, skill_list in skills.items():
        if category == 'programming' and skill_list:
            questions.append(f"I see you have experience with {', '.join(skill_list[:3])}. Which one are you most proficient in?")
        
        if category == 'frameworks' and skill_list:
            questions.append(f"Could you share a project where you used {skill_list[0]}?")
        
        if category == 'databases' and skill_list:
            questions.append(f"How experienced are you with {', '.join(skill_list)}?")
        
        if category == 'cloud' and skill_list:
            questions.append(f"Have you worked with {skill_list[0]} in a production environment?")
        
        if category == 'soft_skills' and skill_list:
            questions.append("Can you give an example of how you've demonstrated leadership in your previous roles?")
    
    return questions

# Streamlit App
st.title("Resume Processing Chatbot")

# Step 1: Upload Resume
st.header("Step 1: Upload Resume")
uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx", "txt"])

if uploaded_file is not None:
    st.success("File successfully uploaded!")
    
    # Extract text based on file type
    if uploaded_file.name.endswith('.pdf'):
        resume_text = extract_text_from_pdf(uploaded_file)
    elif uploaded_file.name.endswith('.docx'):
        resume_text = extract_text_from_docx(uploaded_file)
    else:  # Assume it's a text file
        resume_text = uploaded_file.read().decode()
    
    # Step 2: Extract Skills
    st.header("Step 2: Extracted Skills")
    skills = extract_skills(resume_text)
    
    if skills:
        for category, skill_list in skills.items():
            st.subheader(category.capitalize())
            st.write(", ".join(skill_list))
    else:
        st.warning("No specific skills were identified. Please check the resume format.")
    
    # Step 3: Ask Questions
    st.header("Step 3: Interview Questions")
    questions = generate_questions(skills)
    
    for i, question in enumerate(questions, 1):
        st.write(f"{i}. {question}")
    
    # Simple chat interface
    st.header("Chat Interface")
    st.info("You can use the questions above to interview the candidate.")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask a question:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Simple response (in a real app, this would be more sophisticated)
        with st.chat_message("assistant"):
            response = f"Please provide your answer to: {prompt}"
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
