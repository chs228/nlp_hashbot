import re
import streamlit as st
import io
import base64

# We'll use simpler libraries to avoid dependencies
# For PDF processing
try:
    import PyPDF2
except ImportError:
    st.error("PyPDF2 is not installed. Please install it with: pip install PyPDF2")

# For DOCX processing
try:
    import docx
except ImportError:
    st.error("python-docx is not installed. Please install it with: pip install python-docx")

# Define skills dictionary - simplified version
COMMON_SKILLS = {
    'programming': ['python', 'java', 'javascript', 'html', 'css', 'c++', 'c#', 'ruby', 'php', 'sql', 'r'],
    'frameworks': ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'node.js', 'express', '.net'],
    'databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'sqlite', 'redis'],
    'cloud': ['aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes'],
    'tools': ['git', 'github', 'jira', 'jenkins', 'agile', 'scrum'],
    'soft_skills': ['communication', 'leadership', 'teamwork', 'problem solving', 'time management'],
}

def extract_text_from_pdf(pdf_file):
    """Extract text from a PDF file using a more robust approach."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() or ""  # Handle if extract_text returns None
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

def generate_questions(skills):
    """Generate questions based on identified skills."""
    questions = []
    
    # General questions
    questions.append("Could you tell me more about your experience?")
    questions.append("What are you looking for in your next role?")
    
    # Add skill-specific questions
    if not skills:
        questions.append("Can you share more about your technical skills that aren't mentioned in your resume?")
        return questions
    
    for category, skill_list in skills.items():
        if not skill_list:
            continue
            
        if category == 'programming' and skill_list:
            skills_str = ', '.join(skill_list[:3])
            questions.append(f"I see you have experience with {skills_str}. Which one are you most proficient in?")
        
        if category == 'frameworks' and skill_list:
            questions.append(f"Could you share a project where you used {skill_list[0]}?")
        
        if category == 'databases' and skill_list:
            questions.append(f"How experienced are you with {', '.join(skill_list)}?")
        
        if category == 'cloud' and skill_list:
            questions.append(f"Have you worked with {skill_list[0]} in a production environment?")
        
        if category == 'soft_skills' and skill_list:
            questions.append("Can you give an example of how you've demonstrated leadership in your previous roles?")
    
    return questions

def get_download_link(text, filename, label="Download processed text"):
    """Generate a download link for text file."""
    b64 = base64.b64encode(text.encode()).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">{label}</a>'
    return href

# Streamlit App
st.set_page_config(page_title="Resume Processing Chatbot", layout="wide")
st.title("Resume Processing Chatbot")

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

# Create sidebar for the workflow steps
with st.sidebar:
    st.header("Workflow")
    st.write("1. Upload Resume")
    st.write("2. Extract Skills")
    st.write("3. Ask Questions")
    
    if st.session_state.current_step > 1:
        if st.button("Start Over"):
            st.session_state.resume_text = ""
            st.session_state.skills = {}
            st.session_state.questions = []
            st.session_state.messages = []
            st.session_state.current_step = 1
            st.experimental_rerun()

# Step 1: Upload Resume
if st.session_state.current_step == 1:
    st.header("Step 1: Upload Resume")
    uploaded_file = st.file_uploader("Choose a resume file", type=["pdf", "docx", "txt"])
    
    # Alternative direct text input
    text_input = st.text_area("Or paste resume text directly:", height=200)
    
    col1, col2 = st.columns(2)
    with col1:
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
            st.experimental_rerun()
            
        elif text_input:
            st.session_state.resume_text = text_input
            st.session_state.current_step = 2
            st.experimental_rerun()
            
        else:
            st.error("Please upload a file or paste text to continue.")

# Step 2: Extract Skills
elif st.session_state.current_step == 2:
    st.header("Step 2: Extracted Skills")
    
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
        for category, skill_list in skills.items():
            st.subheader(category.capitalize())
            st.write(", ".join(skill_list))
    else:
        st.warning("No specific skills were identified. The system will use general questions.")
    
    # Manual skill entry
    st.subheader("Add Additional Skills")
    new_skill = st.text_input("Enter a skill that's missing:")
    skill_category = st.selectbox("Category:", list(COMMON_SKILLS.keys()))
    
    if st.button("Add Skill") and new_skill:
        if skill_category in st.session_state.skills:
            if new_skill not in st.session_state.skills[skill_category]:
                st.session_state.skills[skill_category].append(new_skill)
        else:
            st.session_state.skills[skill_category] = [new_skill]
        st.experimental_rerun()
    
    if st.button("Continue to Questions"):
        st.session_state.current_step = 3
        # Generate questions based on skills
        st.session_state.questions = generate_questions(st.session_state.skills)
        st.experimental_rerun()

# Step 3: Ask Questions
elif st.session_state.current_step == 3:
    st.header("Step 3: Interview Questions")
    
    # Display generated questions
    for i, question in enumerate(st.session_state.questions, 1):
        st.write(f"{i}. {question}")
    
    # Allow adding custom questions
    st.subheader("Add Custom Question")
    custom_question = st.text_input("Enter your question:")
    if st.button("Add Question") and custom_question:
        st.session_state.questions.append(custom_question)
        st.experimental_rerun()
    
    # Chat interface
    st.header("Chat Interface")
    st.info("You can use the questions above to interview the candidate.")
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    prompt = st.chat_input("Ask a question:")
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Simple response (in a real app, this would connect to a chatbot backend)
        response = "Please provide your answer to this question."
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.experimental_rerun()
    
    # Export options
    st.subheader("Export Data")
    if st.button("Export Resume Analysis"):
        export_text = "Resume Analysis\n\n"
        export_text += "Extracted Skills:\n"
        for category, skill_list in st.session_state.skills.items():
            export_text += f"{category.capitalize()}: {', '.join(skill_list)}\n"
        
        export_text += "\nGenerated Questions:\n"
        for i, question in enumerate(st.session_state.questions, 1):
            export_text += f"{i}. {question}\n"
        
        export_text += "\nChat History:\n"
        for message in st.session_state.messages:
            export_text += f"{message['role'].capitalize()}: {message['content']}\n"
        
        st.markdown(get_download_link(export_text, "resume_analysis.txt"), unsafe_allow_html=True)
