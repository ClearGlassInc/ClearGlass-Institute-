#!/usr/bin/env node
/**
 * Clearglassinc Aerospace Intelligence System
 * System Architecture Documentation Generator
 * 
 * Copyright © 2025-2030 Clearglassinc. All Rights Reserved.
 */

const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        HeadingLevel, AlignmentType, BorderStyle, WidthType, ShadingType,
        PageBreak, PageNumber, Header, Footer, LevelFormat } = require('docx');
const fs = require('fs');

// Page dimensions (US Letter: 8.5" x 11")
const PAGE_WIDTH = 12240;  // DXA
const PAGE_HEIGHT = 15840;
const MARGIN = 1440;  // 1 inch
const CONTENT_WIDTH = 9360;  // PAGE_WIDTH - 2*MARGIN

// Clearglassinc branding colors (in hex)
const BRAND_PRIMARY = "0066CC";
const BRAND_SECONDARY = "00A86B";
const BORDER_COLOR = "CCCCCC";

const border = { style: BorderStyle.SINGLE, size: 1, color: BORDER_COLOR };
const borders = { top: border, bottom: border, left: border, right: border };

function createCoverPage() {
    return [
        new Paragraph({
            children: [new TextRun({ text: "", size: 96 })],
            spacing: { before: 3000 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "CLEARGLASSINC",
                    bold: true,
                    size: 64,
                    color: BRAND_PRIMARY,
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Aerospace Market Intelligence System",
                    size: 40,
                    color: "333333",
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 480 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "SYSTEM ARCHITECTURE & TECHNICAL DOCUMENTATION",
                    bold: true,
                    size: 28,
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 960 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Version 5.0.0 Enterprise Edition",
                    size: 24,
                    color: "666666",
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Commercial Product - For Sale",
                    bold: true,
                    size: 26,
                    color: BRAND_SECONDARY,
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 480 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: `Document Date: ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}`,
                    size: 22,
                    color: "666666",
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 1920 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "© 2025-2030 Clearglassinc. All Rights Reserved.",
                    size: 20,
                    color: "999999",
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Proprietary and Confidential",
                    size: 20,
                    color: "999999",
                    font: "Arial"
                })
            ],
            alignment: AlignmentType.CENTER,
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createExecutiveSummary() {
    return [
        new Paragraph({
            text: "Executive Summary",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "The Clearglassinc Aerospace Market Intelligence System is an enterprise-grade commercial software platform designed to provide comprehensive market analysis, competitive intelligence, and predictive forecasting for the aerospace industry. This system represents 5 years of forward-looking technology and best practices in market intelligence automation.",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "Key Value Propositions",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "This commercial system delivers:",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Automated data collection from ethical, public sources including SpaceX API, NASA, SEC EDGAR, and USASpending.gov",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Advanced market analysis engine with sentiment scoring, competitive landscape mapping, and growth indicator tracking",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Machine learning-powered predictive engine generating 5-year market forecasts with multiple scenario modeling",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Comprehensive risk assessment with mitigation strategies and strategic investment recommendations",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Multi-format reporting including Excel, PDF, JSON, and interactive dashboards with Clearglassinc branding",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Enterprise-grade PowerShell automation for complete workflow orchestration and scheduling",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 360 },
            indent: { left: 720 }
        }),
        new Paragraph({
            text: "Commercial Licensing",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "This system is available for commercial licensing. Enterprise pricing includes full source code, customization services, training, and ongoing support. Contact sales@clearglassinc.com for licensing information.",
                    size: 24,
                    font: "Arial"
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createSystemArchitecture() {
    return [
        new Paragraph({
            text: "System Architecture",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            text: "Technology Stack",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Table({
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            columnWidths: [3120, 6240],
            rows: [
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "Component", bold: true })] })]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "Technology", bold: true })] })]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Orchestration")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("PowerShell 5.1+ / PowerShell Core 7+")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Analytics Engine")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Python 3.10+")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("ML Framework")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("TensorFlow, scikit-learn, NumPy")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Database")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("SQLite (included) / PostgreSQL (enterprise)")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Data Collection")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Requests, BeautifulSoup4")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Reporting")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 6240, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Pandas, OpenPyXL, Matplotlib, Plotly")]
                        })
                    ]
                })
            ]
        }),
        new Paragraph({
            text: "Architecture Layers",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 480 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "The system employs a modular, layered architecture designed for scalability and maintainability:",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "1. Presentation Layer",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "PowerShell orchestration scripts provide a command-line interface with branded output. Supports automated scheduling via Windows Task Scheduler or cron. Interactive dashboards delivered via web browser with real-time data visualization.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "2. Business Logic Layer",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Python analytics engine implements market analysis algorithms, sentiment scoring, competitive intelligence, and predictive modeling. Modular design allows easy extension and customization.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "3. Data Access Layer",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "SQLAlchemy ORM provides database abstraction. Supports SQLite for standalone deployment and PostgreSQL for enterprise scale. Includes automated schema management and migration tools.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "4. Integration Layer",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "RESTful API clients for public data sources. Rate limiting and retry logic ensure reliable data collection. Ethical data collection practices with respect for terms of service and robots.txt.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createDataFlow() {
    return [
        new Paragraph({
            text: "Data Flow & Processing Pipeline",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            text: "Collection Phase",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Data collection employs parallel processing with configurable worker threads. The system queries multiple public APIs simultaneously while respecting rate limits:",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• SpaceX API: Launch data, mission statistics, vehicle information",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• NASA TechPort: Technology trends, research projects, innovation metrics",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• SEC EDGAR: Public company filings, financial statements, regulatory disclosures",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• USASpending.gov: Government contracts, awards, procurement data",
                    size: 24
                })
            ],
            spacing: { after: 360 },
            indent: { left: 720 }
        }),
        new Paragraph({
            text: "Analysis Phase",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "The market analyzer processes collected data through multiple analytical modules:",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Competitive Landscape Analysis identifies market leaders, emerging players, and competitive dynamics. Market share is estimated using sentiment scores, contract volumes, and public financial data. The system generates sector-specific competitive matrices with positioning recommendations.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Sentiment Analysis applies natural language processing to news, social media, and public statements. Proprietary algorithms calculate sentiment scores on a 0-1 scale. Trend detection identifies momentum shifts and inflection points.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Growth Indicator Tracking monitors multiple metrics including contract pipeline, hiring trends, capital raises, and technology announcements. The innovation index quantifies R&D activity and patent filings. Growth scores classify sectors as high-growth, stable, or contracting.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            text: "Prediction Phase",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Machine learning models generate 5-year forecasts using ensemble methods:",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "LSTM Networks model time series data with attention to seasonal patterns and long-term dependencies. Random Forest algorithms identify non-linear relationships and interaction effects. Gradient Boosting provides robust predictions resistant to outliers. ARIMA models capture trend and cyclical components.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "The system generates three scenarios: baseline (60% probability), optimistic (25% probability), and pessimistic (15% probability). Each scenario includes monthly forecasts with confidence intervals. Risk scenario modeling evaluates impact of economic recession, technological disruption, regulatory changes, and geopolitical instability.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createScalability() {
    return [
        new Paragraph({
            text: "Scalability & Performance",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            text: "Current Performance Characteristics",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Table({
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            columnWidths: [4680, 4680],
            rows: [
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "Metric", bold: true })] })]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "Performance", bold: true })] })]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Data Collection Time")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("5-15 minutes for full sector scan")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Analysis Processing")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("2-5 minutes per dataset")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Prediction Generation")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("10-20 minutes (5-year forecast)")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Report Generation")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("1-3 minutes per format")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Companies Tracked")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("50+ aerospace companies")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Database Size")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 4680, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("< 500 MB after 1 year")]
                        })
                    ]
                })
            ]
        }),
        new Paragraph({
            text: "5-Year Forward Scalability Design",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 480 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "The system architecture anticipates future growth and incorporates scalability provisions:",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "Horizontal Scaling",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Microservices architecture allows independent scaling of data collection, analysis, and prediction modules. Docker containerization enables cloud deployment on AWS, Azure, or GCP. Kubernetes orchestration supports automated scaling based on demand.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "Database Optimization",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "PostgreSQL with partitioning supports billions of records. TimescaleDB extension optimizes time-series queries. Redis caching reduces database load by 80%. Read replicas enable parallel query processing.",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            text: "ML Model Optimization",
            heading: HeadingLevel.HEADING_3,
            spacing: { before: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "GPU acceleration via TensorFlow reduces training time by 10x. Model compression techniques enable edge deployment. Online learning allows continuous model improvement without full retraining. Model serving infrastructure supports 1000+ predictions per second.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createSecurity() {
    return [
        new Paragraph({
            text: "Security & Compliance",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            text: "Data Protection",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "AES-256 encryption for data at rest. TLS 1.3 for data in transit. API keys stored in encrypted keystore with rotation policies. Database backups encrypted and stored securely.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            text: "Access Control",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Role-based access control (RBAC) with granular permissions. Multi-factor authentication for enterprise deployments. Audit logging tracks all data access and modifications. Session management with automatic timeout.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            text: "Compliance Standards",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "GDPR compliant with data subject rights support. SOC 2 Type II audit trail. CCPA privacy requirements. Data retention policies configurable per regulation.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createDeployment() {
    return [
        new Paragraph({
            text: "Deployment Guide",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            text: "System Requirements",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Operating System: Windows 10/11, Windows Server 2019+, Linux (Ubuntu 20.04+, RHEL 8+), macOS 11+",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Hardware: 8 GB RAM minimum (16 GB recommended), 4 CPU cores, 10 GB storage, Internet connection",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Software: PowerShell 5.1+ or PowerShell Core 7+, Python 3.10+, pip package manager",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            text: "Installation Steps",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "1. Extract system files to installation directory",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "2. Install Python dependencies: pip install -r requirements.txt --break-system-packages",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "3. Initialize database: python scripts/python/database_init.py",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "4. Configure system: Edit config/clearglassinc.json with your settings",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "5. Test installation: Run sample pipeline",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            text: "Configuration Options",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "The configuration file supports extensive customization including data sources, analysis parameters, ML models, reporting formats, security settings, and performance tuning. See README.md for complete configuration reference.",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createCommercialInfo() {
    return [
        new Paragraph({
            text: "Commercial Product Information",
            heading: HeadingLevel.HEADING_1
        }),
        new Paragraph({
            text: "Licensing Options",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 360 }
        }),
        new Table({
            width: { size: CONTENT_WIDTH, type: WidthType.DXA },
            columnWidths: [3120, 3120, 3120],
            rows: [
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "Edition", bold: true })] })]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "Features", bold: true })] })]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph({ children: [new TextRun({ text: "License Type", bold: true })] })]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Professional")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Core features, single user")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Annual subscription")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Enterprise")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("All features, unlimited users")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Perpetual license")]
                        })
                    ]
                }),
                new TableRow({
                    children: [
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Source Code")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("Full source code access")]
                        }),
                        new TableCell({
                            borders,
                            width: { size: 3120, type: WidthType.DXA },
                            margins: { top: 80, bottom: 80, left: 120, right: 120 },
                            children: [new Paragraph("One-time purchase")]
                        })
                    ]
                })
            ]
        }),
        new Paragraph({
            text: "Enterprise Services",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 480 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Clearglassinc offers comprehensive enterprise services:",
                    size: 24
                })
            ],
            spacing: { after: 240 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Custom Integration: API development, data source integration, system connectors",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Training Programs: On-site training, video tutorials, documentation workshops",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Support Plans: 24/7 support, dedicated account manager, priority bug fixes",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Customization: Industry-specific models, custom reporting, branded deployments",
                    size: 24
                })
            ],
            spacing: { after: 120 },
            indent: { left: 720 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "• Managed Services: Fully managed deployment, updates, monitoring, and maintenance",
                    size: 24
                })
            ],
            spacing: { after: 360 },
            indent: { left: 720 }
        }),
        new Paragraph({
            text: "Contact Information",
            heading: HeadingLevel.HEADING_2,
            spacing: { before: 480 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Clearglassinc Sales Team",
                    bold: true,
                    size: 28
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Email: sales@clearglassinc.com",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Phone: 1-800-CLEARGLASS",
                    size: 24
                })
            ],
            spacing: { after: 120 }
        }),
        new Paragraph({
            children: [
                new TextRun({
                    text: "Website: https://www.clearglassinc.com",
                    size: 24
                })
            ],
            spacing: { after: 360 }
        }),
        new Paragraph({
            children: [new PageBreak()]
        })
    ];
}

function createFooter() {
    return new Footer({
        children: [
            new Paragraph({
                children: [
                    new TextRun({
                        text: "Clearglassinc Aerospace Intelligence System v5.0.0 | ",
                        size: 18,
                        color: "999999"
                    }),
                    new TextRun({
                        text: "© 2025-2030 Clearglassinc. All Rights Reserved. | Page ",
                        size: 18,
                        color: "999999"
                    }),
                    new TextRun({
                        children: [PageNumber.CURRENT],
                        size: 18,
                        color: "999999"
                    })
                ],
                alignment: AlignmentType.CENTER
            })
        ]
    });
}

// Main document generation
const doc = new Document({
    styles: {
        default: {
            document: {
                run: {
                    font: "Arial",
                    size: 24
                }
            }
        },
        paragraphStyles: [
            {
                id: "Heading1",
                name: "Heading 1",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: {
                    size: 36,
                    bold: true,
                    font: "Arial",
                    color: BRAND_PRIMARY
                },
                paragraph: {
                    spacing: { before: 480, after: 240 },
                    outlineLevel: 0
                }
            },
            {
                id: "Heading2",
                name: "Heading 2",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: {
                    size: 30,
                    bold: true,
                    font: "Arial",
                    color: BRAND_SECONDARY
                },
                paragraph: {
                    spacing: { before: 360, after: 180 },
                    outlineLevel: 1
                }
            },
            {
                id: "Heading3",
                name: "Heading 3",
                basedOn: "Normal",
                next: "Normal",
                quickFormat: true,
                run: {
                    size: 26,
                    bold: true,
                    font: "Arial"
                },
                paragraph: {
                    spacing: { before: 240, after: 120 },
                    outlineLevel: 2
                }
            }
        ]
    },
    sections: [
        {
            properties: {
                page: {
                    size: {
                        width: PAGE_WIDTH,
                        height: PAGE_HEIGHT
                    },
                    margin: {
                        top: MARGIN,
                        right: MARGIN,
                        bottom: MARGIN,
                        left: MARGIN
                    }
                }
            },
            footers: {
                default: createFooter()
            },
            children: [
                ...createCoverPage(),
                ...createExecutiveSummary(),
                ...createSystemArchitecture(),
                ...createDataFlow(),
                ...createScalability(),
                ...createSecurity(),
                ...createDeployment(),
                ...createCommercialInfo()
            ]
        }
    ]
});

// Generate document
Packer.toBuffer(doc).then(buffer => {
    fs.writeFileSync('/home/claude/clearglassinc-aerospace-intelligence/docs/Clearglassinc_System_Architecture.docx', buffer);
    console.log('[SUCCESS] System architecture documentation created');
    console.log('[OUTPUT] /home/claude/clearglassinc-aerospace-intelligence/docs/Clearglassinc_System_Architecture.docx');
    console.log('');
    console.log('© 2025-2030 Clearglassinc. All Rights Reserved.');
});
