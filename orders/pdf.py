from io import BytesIO
from django.utils import timezone
from store.models import Order
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


pdfmetrics.registerFont(
    TTFont("Arial", r"C:\Windows\Fonts\arial.ttf")
)

pdfmetrics.registerFont(
    TTFont("Arial-Bold", r"C:\Windows\Fonts\arialbd.ttf")
)

registerFontFamily(
    "Arial",
    normal="Arial",
    bold="Arial-Bold",
    italic="Arial",
    boldItalic="Arial-Bold",
)


def generate_order_pdf(order: Order) -> bytes:
    """Generate a business order PDF from a saved order."""
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"SHIMA ESSENTIALS Order {order.order_number}",
    )
    
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "Arial"
    styles["Heading2"].fontName = "Arial-Bold"
    styles.add(
        ParagraphStyle(
            name="BusinessTitle",
            parent=styles["Title"],
            alignment=TA_CENTER,
            textColor=colors.HexColor("#6B3E26"),
        )
    )

    story = [
        Paragraph("SHIMA ESSENTIALS", styles["BusinessTitle"]),
        Paragraph("Style. Taste. Essentials.", styles["Normal"]),
        Paragraph("Everyday Elegance.", styles["Normal"]),
        Spacer(1, 8 * mm),
        Paragraph(f"Order: {order.order_number}", styles["Heading2"]),
        Paragraph(
            f"Date: {timezone.localtime(order.created_at).strftime('%d %b %Y, %I:%M %p')}",
            styles["Normal"],
        ),
        Paragraph(f"Status: {order.get_status_display()}", styles["Normal"]),
        Spacer(1, 5 * mm),
        Paragraph("Customer Details", styles["Heading2"]),
        Paragraph(f"Name: {order.customer_name}", styles["Normal"]),
        Paragraph(f"Phone: {order.phone}", styles["Normal"]),
        Paragraph(f"Delivery location: {order.delivery_location}", styles["Normal"]),
        Paragraph(f"Address: {order.address}", styles["Normal"]),
    ]

    if order.notes:
        story.extend(
            [
                Paragraph("Order Notes", styles["Heading2"]),
                Paragraph(order.notes, styles["Normal"]),
            ]
        )

    story.extend(
        [
            Spacer(1, 5 * mm),
            Paragraph("Order Items", styles["Heading2"]),
        ]
    )

    rows = [
        ["Product", "Qty", "Unit Price", "Line Total"],
    ]

    for item in order.items.all():
        rows.append(
            [
                item.product_name_snapshot,
                str(item.quantity),
                f"₦{item.unit_price:,.2f}",
                f"₦{item.line_total:,.2f}",
            ]
        )

    table = Table(
        rows,
        colWidths=[75 * mm, 15 * mm, 35 * mm, 35 * mm],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#6B3E26")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 1), (-1, -1), "Arial"),
                ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    story.extend([table, Spacer(1, 5 * mm)])

    totals = [
        ["Subtotal", f"₦{order.subtotal:,.2f}"],
        ["Delivery fee", f"₦{order.delivery_fee:,.2f}"],
        ["Total", f"₦{order.total:,.2f}"],
    ]

    totals_table = Table(totals, colWidths=[120 * mm, 40 * mm])
    totals_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#6B3E26")),
                ("FONTNAME", (0, 0), (-1, -2), "Arial"),
                ("FONTNAME", (0, -1), (-1, -1), "Arial-Bold"),
            ]
        )
    )
    story.append(totals_table)

    document.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()

    return pdf_bytes
