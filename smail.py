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
# from smail import export_results_to_email

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

def export_results_to_email(avg_score,rating,skills,interview_date):
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
Overall Score: {avg_score}/100
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
