from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import datetime

class DoctorSummaryPDFService:

    def generate_pdf(self, profile: dict, report_analysis: dict) -> bytes:
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        y = height - 40

        def draw_line(text):
            nonlocal y
            c.drawString(40, y, text)
            y -= 18
            if y < 40:
                c.showPage()
                y = height - 40

        # Header
        draw_line("Doctor Summary Report")
        draw_line(f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        draw_line("-" * 80)

        # Profile
        draw_line("Patient Profile")
        draw_line(f"Age: {profile.get('age', 'N/A')}")
        draw_line(f"Gender: {profile.get('gender', 'N/A')}")
        draw_line(f"Allergies: {', '.join(profile.get('allergies', [])) or 'None'}")
        draw_line(f"Chronic Conditions: {', '.join(profile.get('chronic_conditions', [])) or 'None'}")
        draw_line(f"Active Medications: {', '.join(profile.get('active_medications', [])) or 'None'}")
        draw_line("")

        # Medical Summary
        draw_line("Medical Summary")
        draw_line(profile.get("medical_summary", "No summary available."))
        draw_line("")

        # Report Summary
        draw_line("Latest Report Analysis")
        draw_line(report_analysis.get("summary", ""))
        draw_line("")

        # Key Findings
        draw_line("Key Findings")
        for k, v in report_analysis.get("key_findings", {}).items():
            draw_line(f"- {k}: {str(v)[:200]}")

        draw_line("")
        draw_line("⚠️ Disclaimer")
        draw_line(
            "This document is AI-generated for informational purposes only and "
            "does not constitute a medical diagnosis. A licensed physician must "
            "interpret this information."
        )

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()