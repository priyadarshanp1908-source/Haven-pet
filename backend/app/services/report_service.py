"""Report service — generate CSV and PDF exports of pet history."""

import csv
import io
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.pet import Pet
from app.models.behavior_log import BehaviorLog
from app.models.vaccination import Vaccination
from app.models.medication import Medication


async def generate_csv_report(pet_id: str, db: AsyncSession) -> str:
    """Generate a CSV string containing behavior logs, vaccinations, and medications."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Behavior Logs section
    writer.writerow(["=== Behavior Logs ==="])
    writer.writerow(["Date", "Category", "Value", "Notes", "Anomaly"])
    result = await db.execute(
        select(BehaviorLog)
        .where(BehaviorLog.pet_id == pet_id)
        .order_by(BehaviorLog.logged_at.desc())
    )
    for log in result.scalars().all():
        writer.writerow([
            log.logged_at.isoformat() if log.logged_at else "",
            log.category,
            log.value or "",
            log.notes or "",
            "Yes" if log.flagged_anomaly else "No",
        ])

    writer.writerow([])

    # Vaccinations section
    writer.writerow(["=== Vaccinations ==="])
    writer.writerow(["Vaccine", "Date Administered", "Next Due Date"])
    result = await db.execute(
        select(Vaccination)
        .where(Vaccination.pet_id == pet_id)
        .order_by(Vaccination.date_administered.desc())
    )
    for vax in result.scalars().all():
        writer.writerow([
            vax.vaccine_name,
            vax.date_administered.isoformat() if vax.date_administered else "",
            vax.next_due_date.isoformat() if vax.next_due_date else "",
        ])

    writer.writerow([])

    # Medications section
    writer.writerow(["=== Medications ==="])
    writer.writerow(["Name", "Dosage", "Schedule", "Start Date", "End Date", "Notes"])
    result = await db.execute(
        select(Medication)
        .where(Medication.pet_id == pet_id)
        .order_by(Medication.start_date.desc())
    )
    for med in result.scalars().all():
        writer.writerow([
            med.name,
            med.dosage,
            med.schedule,
            med.start_date.isoformat() if med.start_date else "",
            med.end_date.isoformat() if med.end_date else "",
            med.notes or "",
        ])

    return output.getvalue()


async def generate_pdf_report(pet_id: str, db: AsyncSession) -> bytes:
    """Generate a PDF report of pet history using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch)
    styles = getSampleStyleSheet()
    elements = []

    # Get pet info
    result = await db.execute(select(Pet).where(Pet.id == pet_id))
    pet = result.scalar_one_or_none()
    pet_name = pet.name if pet else "Unknown"

    # Title
    elements.append(Paragraph(f"Haven Pet — Report for {pet_name}", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]))
    elements.append(Spacer(1, 20))

    # Behavior Logs
    elements.append(Paragraph("Behavior Logs", styles["Heading2"]))
    result = await db.execute(
        select(BehaviorLog)
        .where(BehaviorLog.pet_id == pet_id)
        .order_by(BehaviorLog.logged_at.desc())
        .limit(50)
    )
    logs = result.scalars().all()
    if logs:
        data = [["Date", "Category", "Value", "Anomaly"]]
        for log in logs:
            data.append([
                log.logged_at.strftime("%Y-%m-%d %H:%M") if log.logged_at else "",
                log.category,
                (log.value or "")[:30],
                "⚠" if log.flagged_anomaly else "✓",
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No behavior logs recorded.", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # Vaccinations
    elements.append(Paragraph("Vaccinations", styles["Heading2"]))
    result = await db.execute(
        select(Vaccination).where(Vaccination.pet_id == pet_id).order_by(Vaccination.date_administered.desc())
    )
    vaxes = result.scalars().all()
    if vaxes:
        data = [["Vaccine", "Administered", "Next Due"]]
        for v in vaxes:
            data.append([
                v.vaccine_name,
                v.date_administered.isoformat() if v.date_administered else "",
                v.next_due_date.isoformat() if v.next_due_date else "N/A",
            ])
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No vaccinations recorded.", styles["Normal"]))

    elements.append(Spacer(1, 20))

    # Medications
    elements.append(Paragraph("Medications", styles["Heading2"]))
    result = await db.execute(
        select(Medication).where(Medication.pet_id == pet_id).order_by(Medication.start_date.desc())
    )
    meds = result.scalars().all()
    if meds:
        data = [["Name", "Dosage", "Schedule", "Period"]]
        for m in meds:
            period = f"{m.start_date.isoformat()} → {m.end_date.isoformat() if m.end_date else 'ongoing'}"
            data.append([m.name, m.dosage, m.schedule, period])
        table = Table(data)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6366f1")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No medications recorded.", styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()
