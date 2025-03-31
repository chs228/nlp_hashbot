from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
import streamlit as st

def generate_interview_results_pdf(interview_data):
    """Generate a PDF with interview results using ReportLab."""
    try:
        date = interview_data.get("date", "Not specified")
        overall_score = interview_data.get("overall_score", 0)
        rating = interview_data.get("rating", "Not rated")
        skills = interview_data.get("skills", {})
        questions = interview_data.get("questions", [])
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
        
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading2_style = styles['Heading2']
        normal_style = styles['Normal']
        
        feedback_style = ParagraphStyle('Feedback', parent=normal_style, spaceAfter=6, leftIndent=20)
        elements = []
        
        elements.append(Paragraph("Technical Interview Results", title_style))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"<b>Date:</b> {date}", normal_style))
        elements.append(Paragraph(f"<b>Overall Score:</b> {overall_score:.1f}/100", normal_style))
        elements.append(Paragraph(f"<b>Rating:</b> {rating}", normal_style))
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("Extracted Skills", heading2_style))
        if skills:
            skill_data = [['Category', 'Skills']]
            for category, skill_list in skills.items():
                skill_data.append([category.capitalize(), ", ".join(skill_list)])
            
            skill_table = Table(skill_data, colWidths=[100, 350])
            skill_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (1, 0), colors.black),
                ('ALIGN', (0, 0), (1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(skill_table)
        else:
            elements.append(Paragraph("No skills were identified.", normal_style))
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph("Interview Questions and Evaluations", heading2_style))
        elements.append(Spacer(1, 12))
        
        for q in questions:
            question_text = q.get("question_text", "")
            question_number = q.get("question_number", "")
            answer = q.get("answer", "")
            score = q.get("score", 0)
            feedback = q.get("feedback", "No feedback available")
            missing_concepts = q.get("missing_concepts", [])
            
            score_text = f"<b>Score:</b> "
            if score >= 80:
                score_text += f"<font color='green'>{score}/100</font>"
            elif score >= 60:
                score_text += f"<font color='orange'>{score}/100</font>"
            else:
                score_text += f"<font color='red'>{score}/100</font>"
            
            elements.append(Paragraph(f"<b>Question {question_number}:</b> {question_text}", styles['Heading3']))
            elements.append(Paragraph(f"<b>Answer:</b> {answer}", normal_style))
            elements.append(Paragraph(score_text, normal_style))
            elements.append(Paragraph(f"<b>Feedback:</b> {feedback}", normal_style))
            
            if missing_concepts:
                elements.append(Paragraph("<b>Missing concepts:</b>", normal_style))
                for concept in missing_concepts:
                    elements.append(Paragraph(f"• {concept}", feedback_style))
            
            elements.append(Spacer(1, 20))
        
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
    
    except Exception as e:
        st.error(f"Error generating PDF: {str(e)}")
        return None

def export_results_to_email(avg_score, rating, skills, interview_date):
    recipient_email = st.text_input("Recipient Email")
    email_subject = st.text_input("Email Subject", f"Technical Interview Results - {interview_date}")
    
    if st.button("Send Results via Email"):
        if recipient_email:
            interview_data = {
                "date": interview_date,
                "overall_score": avg_score,
                "rating": rating,
                "skills": skills,
                "questions": []
            }
            
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
            
            pdf_data = generate_interview_results_pdf(interview_data)
            
            if pdf_data:
                email_body = f"""
Technical Interview Results Summary

Date: {interview_date}
Overall Score: {avg_score}/100
Rating: {rating}

The complete interview results are attached as a PDF.
"""
                
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
                st.error("Failed to generate PDF.")
        else:
            st.error("Please enter a recipient email address.")
