import io
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def create_volumetric_report_pdf(vol_gas_cap, vol_oil_zone, vol_total_res,
                                 goc_input, woc_input,
                                 num_points, x_range, y_range, z_range):
    """Membuat laporan volumetrik dalam format PDF (ringkasan)"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Title
    story.append(Paragraph("Laporan Volumetrik Reservoir", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Date
    date_str = datetime.now().strftime("%d %B %Y, %H:%M:%S")
    story.append(Paragraph(f"<i>Dibuat pada: {date_str}</i>", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Summary
    story.append(Paragraph("Ringkasan Perhitungan", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    summary_data = [
        ['Parameter', 'Nilai'],
        ['Total Data Points', f"{num_points} titik"],
        ['Gas-Oil Contact (GOC)', f"{goc_input:.2f} m"],
        ['Water-Oil Contact (WOC)', f"{woc_input:.2f} m"],
        ['Rentang X', f"{x_range[0]:.2f} - {x_range[1]:.2f}"],
        ['Rentang Y', f"{y_range[0]:.2f} - {y_range[1]:.2f}"],
        ['Rentang Z (Kedalaman)', f"{z_range[0]:.2f} - {z_range[1]:.2f} m"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Volume Results
    story.append(Paragraph("Hasil Perhitungan Volume", styles['Heading2']))
    story.append(Spacer(1, 0.1*inch))
    
    volume_data = [
        ['Zona', 'Volume (m³)', 'Volume (Juta m³)'],
        ['Gas Cap', f"{vol_gas_cap:,.2f}", f"{vol_gas_cap/1e6:.2f}"],
        ['Oil Zone', f"{vol_oil_zone:,.2f}", f"{vol_oil_zone/1e6:.2f}"],
        ['Total Reservoir', f"{vol_total_res:,.2f}", f"{vol_total_res/1e6:.2f}"],
    ]
    
    volume_table = Table(volume_data, colWidths=[2*inch, 2*inch, 2*inch])
    volume_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    story.append(volume_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Notes
    story.append(Paragraph("Catatan:", styles['Heading3']))
    story.append(Paragraph(
        "• Volume dihitung berdasarkan Gross Rock Volume (GRV) menggunakan metode grid interpolation.<br/>"
        "• Gas Cap: Volume batuan di atas GOC<br/>"
        "• Oil Zone: Volume batuan antara GOC dan WOC<br/>"
        "• Total Reservoir: Volume batuan di atas WOC",
        styles['Normal']
    ))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def create_volumetric_report_excel(vol_gas_cap, vol_oil_zone, vol_total_res,
                                   goc_input, woc_input,
                                   num_points, x_range, y_range, z_range, df):
    """Membuat laporan volumetrik dalam format Excel"""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Sheet 1: Summary
        summary_df = pd.DataFrame({
            'Parameter': ['Total Data Points', 'GOC (m)', 'WOC (m)',
                          'X Min', 'X Max', 'Y Min', 'Y Max', 'Z Min (m)', 'Z Max (m)'],
            'Nilai': [num_points, goc_input, woc_input,
                      x_range[0], x_range[1], y_range[0], y_range[1], z_range[0], z_range[1]]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        # Sheet 2: Volume Results
        volume_df = pd.DataFrame({
            'Zona': ['Gas Cap', 'Oil Zone', 'Total Reservoir'],
            'Volume (m³)': [vol_gas_cap, vol_oil_zone, vol_total_res],
            'Volume (Juta m³)': [vol_gas_cap/1e6, vol_oil_zone/1e6, vol_total_res/1e6]
        })
        volume_df.to_excel(writer, sheet_name='Volume Results', index=False)
        
        # Sheet 3: Raw Data
        df.to_excel(writer, sheet_name='Raw Data', index=False)
    
    buffer.seek(0)
    return buffer
