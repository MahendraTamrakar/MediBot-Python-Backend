from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def generate_doctor_summary_pdf(data: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>AI-Generated Medical Summary (For Doctor Review)</b>", styles["Title"]))
    story.append(Spacer(1, 12))

    # Diagnoses
    story.append(Paragraph("<b>AI-Estimated Possible Diagnoses</b>", styles["Heading2"]))
    diagnoses = []
    for d in data.get("ai_estimated_possible_diagnoses", []):
        diagnoses.append(
            f"{d['name']} (Confidence: {d['confidence_level']}) – {d['reasoning']}"
        )
    story.append(ListFlowable(diagnoses, bulletType="bullet"))
    story.append(Spacer(1, 12))

    # Recommendations
    story.append(Paragraph("<b>Recommended Next Steps</b>", styles["Heading2"]))
    story.append(ListFlowable(data.get("recommended_next_steps", []), bulletType="bullet"))
    story.append(Spacer(1, 12))

    # Disclaimer
    story.append(Paragraph("<b>Disclaimer</b>", styles["Heading2"]))
    story.append(Paragraph(data.get("ai_disclaimer", ""), styles["Normal"]))

    doc.build(story)