import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

SUPPLIERS = [
    {
        "name": "Apex Systems",
        "filename": "sample_pdfs/Apex_Systems_Proposal.pdf",
        "content": [
            ("Apex Systems - Enterprise Cloud Architecture & Services RFP", "Title"),
            ("1. Executive Summary", "Heading2"),
            ("Apex Systems delivers resilient, enterprise-grade cloud platforms. We specialize in zero-trust, multi-region architectures with deep integration support.", "Normal"),
            ("2. Proposed Technical Solution", "Heading2"),
            ("Our solution features an asynchronous microservices platform on Kubernetes, active-active failover across multi-region availability zones, and Kafka message brokers capable of over 50,000 ops/sec. Real-time telemetry is integrated with OpenTelemetry.", "Normal"),
            ("3. Security & Compliance", "Heading2"),
            ("Certified in ISO 27001, SOC 2 Type II, and FedRAMP. Our deployment enforces AES-256 at rest, mutual TLS (mTLS) for internal transit, and automated static vulnerability scanning in all deployment pipelines.", "Normal"),
            ("4. Commercial Proposal", "Heading2"),
            ("Total Implementation Cost: $480,000. Ongoing Cloud Support: $35,000/month. Our premium pricing reflects enterprise-tier reliability and guaranteed 99.999% SLA.", "Normal"),
            ("5. Implementation Timeline", "Heading2"),
            ("Total duration: 8 months across 4 major milestones. Staffing includes 8 dedicated senior cloud architects and site reliability engineers.", "Normal"),
            ("6. Experience & Support", "Heading2"),
            ("Over 10 years supporting Fortune 500 financial clients. 24/7 dedicated tier-3 technical account engineering team with a 15-minute SLA on severity-1 incidents.", "Normal")
        ]
    },
    {
        "name": "BrightPath Tech",
        "filename": "sample_pdfs/BrightPath_Tech_Proposal.pdf",
        "content": [
            ("BrightPath Tech - Modern RFP Response", "Title"),
            ("1. Executive Summary", "Heading2"),
            ("BrightPath Tech offers cost-effective, high-velocity digital implementations designed for rapid deployment and maximum ROI.", "Normal"),
            ("2. Proposed Technical Solution", "Heading2"),
            ("Standard cloud-hosted containerized deployment. Basic API integrations and scheduled batch processing for third-party system data exchange.", "Normal"),
            ("3. Security & Compliance", "Heading2"),
            ("Standard HTTPS encryption with basic role-based access control. Formal compliance certifications like SOC 2 and ISO 27001 are currently in planning for future roadmaps.", "Normal"),
            ("4. Commercial Proposal", "Heading2"),
            ("Total Implementation Cost: $180,000. Maintenance: $8,000/month. The most aggressive and accessible pricing structure in the industry.", "Normal"),
            ("5. Implementation Timeline", "Heading2"),
            ("Rapid deployment: Completed within 3 months. Core milestones run concurrently with lean agile teams.", "Normal"),
            ("6. Experience & Support", "Heading2"),
            ("Young boutique consultancy with 2 years of operating history and 4 successful SMB deliveries. Business-hours support via email ticketing.", "Normal")
        ]
    },
    {
        "name": "NexaWorks",
        "filename": "sample_pdfs/NexaWorks_Proposal.pdf",
        "content": [
            ("NexaWorks - Comprehensive Enterprise RFP Response", "Title"),
            ("1. Executive Summary", "Heading2"),
            ("NexaWorks provides a balanced, structured approach combining robust program governance, seamless implementation, and comprehensive ongoing operational care.", "Normal"),
            ("2. Proposed Technical Solution", "Heading2"),
            ("Modern microservices architecture on managed container services. Fully documented REST and GraphQL endpoints with standard caching patterns.", "Normal"),
            ("3. Security & Compliance", "Heading2"),
            ("SOC 2 Type II certified. Annual third-party penetration testing, role-based access management, and full GDPR compliance safeguards.", "Normal"),
            ("4. Commercial Proposal", "Heading2"),
            ("Total Implementation Cost: $310,000. Support: $18,000/month. Transparent fixed-fee milestone model with no hidden charges.", "Normal"),
            ("5. Implementation Timeline", "Heading2"),
            ("Total duration: 5 months. Detailed Gantt milestones, formal RACI matrix, dedicated risk management framework, and weekly steerco meetings.", "Normal"),
            ("6. Experience & Support", "Heading2"),
            ("Award-winning 24/7/365 operational follow-the-sun support team. Extensive track record across 25+ successful mid-market digital transformations.", "Normal")
        ]
    },
    {
        "name": "Orbit Digital",
        "filename": "sample_pdfs/Orbit_Digital_Proposal.pdf",
        "content": [
            ("Orbit Digital - Enterprise RFP Submission", "Title"),
            ("1. Executive Summary", "Heading2"),
            ("Orbit Digital is an industry veteran known for extensive consulting credentials, deep enterprise heritage, and tier-1 corporate partnerships.", "Normal"),
            ("2. Proposed Technical Solution", "Heading2"),
            ("Hybrid cloud configuration utilizing pre-existing corporate software modules. Technical interface adapters will be scoped out during initial discovery workshops.", "Normal"),
            ("3. Security & Compliance", "Heading2"),
            ("ISO 27001 certified data center operations. Standard enterprise governance and periodic network audits.", "Normal"),
            ("4. Commercial Proposal", "Heading2"),
            ("Total Implementation Cost: $340,000. Support: $22,000/month. Time and materials pricing structure for edge-case integration requirements.", "Normal"),
            ("5. Implementation Timeline", "Heading2"),
            ("Estimated at 6 to 7 months, subject to alignment after initial stakeholder workshops.", "Normal"),
            ("6. Experience & Support", "Heading2"),
            ("15+ years in tier-1 enterprise implementations. Strong references from 5 global multi-national corporations. Tier-2 technical support provided during regional business hours.", "Normal")
        ]
    }
]

def generate_all_pdfs():
    os.makedirs("sample_pdfs", exist_ok=True)
    styles = getSampleStyleSheet()

    for item in SUPPLIERS:
        doc = SimpleDocTemplate(item["filename"], pagesize=letter)
        story = []
        for text, style_name in item["content"]:
            style = styles[style_name]
            story.append(Paragraph(text, style))
            story.append(Spacer(1, 10))
        doc.build(story)
        print(f"Generated: {item['filename']}")

if __name__ == "__main__":
    generate_all_pdfs()
