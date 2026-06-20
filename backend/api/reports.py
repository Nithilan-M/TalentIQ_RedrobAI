import csv
from io import StringIO, BytesIO
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database.connection import get_db
from backend.database.models import (
    Candidate, JobDescription, RankingResult, Recommendation, 
    InterviewQuestion, Experience, Education, Project, Certification, User
)
from backend.api.auth import get_current_user

# ReportLab imports for styled PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

router = APIRouter(prefix="/api/export", tags=["Reports"])

@router.get("/csv")
def export_csv(
    job_description_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export ranked candidate listings for a job description as a CSV file.
    """
    # Verify job description
    jd = db.query(JobDescription).filter(JobDescription.id == job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job description not found"
        )

    candidates = db.query(Candidate).filter(Candidate.job_description_id == job_description_id).all()
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidates found to export for this job description."
        )

    # Compile dataset
    rows = []
    for c in candidates:
        rank = db.query(RankingResult).filter(RankingResult.candidate_id == c.id).first()
        rec = db.query(Recommendation).filter(Recommendation.candidate_id == c.id).first()
        
        rows.append({
            "Name": c.name,
            "Email": c.email or "N/A",
            "Phone": c.phone or "N/A",
            "Overall Match Score (%)": rank.overall_score if rank else 0.0,
            "Skill Score": rank.skill_match_score if rank else 0.0,
            "Experience Score": rank.experience_score if rank else 0.0,
            "Project Score": rank.projects_score if rank else 0.0,
            "Education Score": rank.education_score if rank else 0.0,
            "Committee Decision": rec.judge_decision if rec else "N/A",
            "Judge Confidence (%)": rec.judge_confidence if rec else 0.0,
            "Key Skills": ", ".join(c.skills[:10])
        })

    # Sort rows by score descending
    rows.sort(key=lambda x: x["Overall Match Score (%)"], reverse=True)

    # Generate CSV stream
    f = StringIO()
    writer = csv.DictWriter(f, fieldnames=[
        "Name", "Email", "Phone", "Overall Match Score (%)", "Skill Score",
        "Experience Score", "Project Score", "Education Score", 
        "Committee Decision", "Judge Confidence (%)", "Key Skills"
    ])
    writer.writeheader()
    writer.writerows(rows)
    
    # Prepare response
    response_content = f.getvalue()
    f.close()

    filename = f"Candidates_Report_{jd.title.replace(' ', '_')}.csv"
    
    return StreamingResponse(
        iter([response_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/pdf")
def export_pdf(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a high-quality PDF candidate report dossier using ReportLab.
    """
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found."
        )

    # Verify job description ownership
    jd = db.query(JobDescription).filter(JobDescription.id == c.job_description_id, JobDescription.user_id == current_user.id).first()
    if not jd:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized."
        )

    rank = db.query(RankingResult).filter(RankingResult.candidate_id == candidate_id).first()
    rec = db.query(Recommendation).filter(Recommendation.candidate_id == candidate_id).first()
    questions = db.query(InterviewQuestion).filter(InterviewQuestion.candidate_id == candidate_id).first()

    # Create byte buffer for PDF
    buffer = BytesIO()
    
    # Configure document layout
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    # Set styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle', 
        parent=styles['Heading1'], 
        textColor=colors.HexColor('#2A2D34'), 
        fontSize=24, 
        spaceAfter=15
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle', 
        parent=styles['Heading2'], 
        textColor=colors.HexColor('#4E54C8'), 
        fontSize=15, 
        spaceBefore=15, 
        spaceAfter=8,
        borderColor=colors.HexColor('#4E54C8'),
        borderWidth=1,
        borderRadius=2,
        borderPadding=4
    )

    meta_label_style = ParagraphStyle(
        'MetaLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.HexColor('#2A2D34')
    )

    meta_value_style = ParagraphStyle(
        'MetaValue',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555')
    )
    
    body_style = ParagraphStyle(
        'Body', 
        parent=styles['Normal'], 
        fontSize=10, 
        leading=14, 
        textColor=colors.HexColor('#333333'),
        spaceAfter=5
    )
    
    bold_body_style = ParagraphStyle(
        'BoldBody', 
        parent=styles['Normal'], 
        fontName='Helvetica-Bold',
        fontSize=10, 
        leading=14, 
        textColor=colors.HexColor('#333333'),
        spaceAfter=5
    )

    # Flowables list
    elements = []

    # Title & Metadata
    elements.append(Paragraph("AI Hiring Committee - Candidate Dossier", title_style))
    elements.append(Spacer(1, 10))

    # Grid for Candidate & JD general info
    candidate_meta = [
        [Paragraph("Candidate Name:", meta_label_style), Paragraph(c.name, meta_value_style), Paragraph("Target Job Title:", meta_label_style), Paragraph(jd.title, meta_value_style)],
        [Paragraph("Email Address:", meta_label_style), Paragraph(c.email or "N/A", meta_value_style), Paragraph("Industry Domain:", meta_label_style), Paragraph(jd.industry or "N/A", meta_value_style)],
        [Paragraph("Contact Phone:", meta_label_style), Paragraph(c.phone or "N/A", meta_value_style), Paragraph("Evaluation Date:", meta_label_style), Paragraph(c.created_at.strftime('%Y-%m-%d'), meta_value_style)]
    ]
    t_meta = Table(candidate_meta, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F5F7FA')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 20))

    # 1. Committee Consensus Verdict
    elements.append(Paragraph("1. Committee Consensus Verdict", section_title_style))
    verdict = rec.judge_decision if rec else "Borderline"
    confidence = rec.judge_confidence if rec else 50.0
    overall = rank.overall_score if rank else 0.0
    
    # Color coding decisions
    verdict_color = '#E53E3E' # Red
    if verdict == "Strong Hire":
        verdict_color = '#38A169' # Green
    elif verdict == "Hire":
        verdict_color = '#4E54C8' # Purple/Blue
    elif verdict == "Borderline":
        verdict_color = '#DD6B20' # Orange

    verdict_desc_style = ParagraphStyle(
        'VerdictDesc',
        parent=styles['Normal'],
        fontSize=12,
        fontName='Helvetica-Bold',
        textColor=colors.HexColor(verdict_color)
    )

    consensus_summary = [
        [Paragraph("Overall Match Score:", meta_label_style), Paragraph(f"{overall}%", verdict_desc_style), Paragraph("Decision Verdict:", meta_label_style), Paragraph(verdict.upper(), verdict_desc_style)],
        [Paragraph("Judge Confidence:", meta_label_style), Paragraph(f"{confidence}%", meta_value_style), Paragraph("Review Consensus:", meta_label_style), Paragraph(rec.judge_summary if rec else "N/A", meta_value_style)]
    ]
    t_consensus = Table(consensus_summary, colWidths=[1.3*inch, 2.2*inch, 1.3*inch, 2.2*inch])
    t_consensus.setStyle(TableStyle([
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0'))
    ]))
    elements.append(t_consensus)
    elements.append(Spacer(1, 15))

    # 2. Ranking Score Breakdown
    elements.append(Paragraph("2. Skill & Fit Assessment Scores", section_title_style))
    score_breakdown = [
        [Paragraph("Assessment Area", meta_label_style), Paragraph("Score", meta_label_style), Paragraph("Weight", meta_label_style)],
        [Paragraph("Core Skill Match", meta_value_style), Paragraph(f"{rank.skill_match_score}/100" if rank else "0/100", meta_value_style), Paragraph("40%", meta_value_style)],
        [Paragraph("Experience Depth", meta_value_style), Paragraph(f"{rank.experience_score}/100" if rank else "0/100", meta_value_style), Paragraph("20%", meta_value_style)],
        [Paragraph("Projects Strength", meta_value_style), Paragraph(f"{rank.projects_score}/100" if rank else "0/100", meta_value_style), Paragraph("15%", meta_value_style)],
        [Paragraph("Educational Fit", meta_value_style), Paragraph(f"{rank.education_score}/100" if rank else "0/100", meta_value_style), Paragraph("10%", meta_value_style)],
        [Paragraph("Certifications & Badges", meta_value_style), Paragraph(f"{rank.certifications_score}/100" if rank else "0/100", meta_value_style), Paragraph("5%", meta_value_style)],
        [Paragraph("Leadership & Ownership", meta_value_style), Paragraph(f"{rank.leadership_score}/100" if rank else "0/100", meta_value_style), Paragraph("5%", meta_value_style)],
        [Paragraph("Soft Skills & Agility", meta_value_style), Paragraph(f"{rank.soft_skills_score}/100" if rank else "0/100", meta_value_style), Paragraph("5%", meta_value_style)]
    ]
    t_scores = Table(score_breakdown, colWidths=[3.0*inch, 2.0*inch, 2.0*inch])
    t_scores.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4E54C8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    # Quick fix for text color in header
    for i in range(3):
        score_breakdown[0][i].style.textColor = colors.white
    elements.append(t_scores)
    
    # Force Page Break to prevent ugly truncation of debate transcripts
    elements.append(PageBreak())

    # 3. Advocate Testimonial
    elements.append(Paragraph("3. Committee Advocate Report (Key Strengths)", section_title_style))
    adv_text = rec.advocate_feedback if rec else "No advocate feedback recorded."
    # Standard replacement of markdown bullet points to raw paragraphs or list paragraphs
    adv_paras = adv_text.split('\n')
    for p in adv_paras:
        p_clean = p.strip()
        if p_clean.startswith('*') or p_clean.startswith('-'):
            elements.append(Paragraph(f"• {p_clean[1:].strip()}", body_style))
        elif p_clean:
            elements.append(Paragraph(p_clean, body_style))
    elements.append(Spacer(1, 10))

    # 4. Skeptic Critical Review
    elements.append(Paragraph("4. Committee Skeptic Report (Risk Factors)", section_title_style))
    skp_text = rec.skeptic_feedback if rec else "No skeptic feedback recorded."
    skp_paras = skp_text.split('\n')
    for p in skp_paras:
        p_clean = p.strip()
        if p_clean.startswith('*') or p_clean.startswith('-'):
            elements.append(Paragraph(f"• {p_clean[1:].strip()}", body_style))
        elif p_clean:
            elements.append(Paragraph(p_clean, body_style))
    elements.append(Spacer(1, 10))

    # 5. Interview Guide Questions
    if questions and questions.questions:
        elements.append(PageBreak())
        elements.append(Paragraph("5. Interview Copilot - Tailored Interview Guide", section_title_style))
        elements.append(Paragraph("Use these customized questions targeting the candidate's specific skills gaps, projects, and role fit during live screening.", body_style))
        elements.append(Spacer(1, 8))
        
        for idx, q in enumerate(questions.questions):
            q_text = f"Q{idx+1} [{q.get('category')} - {q.get('difficulty')}]: {q.get('question')}"
            elements.append(Paragraph(q_text, bold_body_style))
            elements.append(Paragraph(f"Expected Answer Guidance: {q.get('guidance')}", body_style))
            elements.append(Spacer(1, 6))

    # Build Document
    doc.build(elements)
    
    # Return stream
    pdf_content = buffer.getvalue()
    buffer.close()

    filename = f"Candidate_Dossier_{c.name.replace(' ', '_')}.pdf"
    
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
