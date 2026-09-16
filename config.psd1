# Clearglassinc Aerospace Intelligence System
# Configuration File v2.0
# Copyright (c) 2025-2030 Clearglassinc. All rights reserved.

@{
    # System Information
    SystemName = "Clearglassinc Aerospace Intelligence Platform"
    Version = "2.0.0"
    CompanyName = "Clearglassinc"
    CompanyWebsite = "https://www.clearglassinc.com"
    SupportEmail = "support@clearglassinc.com"
    
    # API Configuration
    APIs = @{
        # LinkedIn API (Requires paid license)
        LinkedIn = @{
            Enabled = $true
            APIKey = $env:LINKEDIN_API_KEY
            RateLimit = 100  # requests per hour
            Timeout = 30000  # milliseconds
        }
        
        # Crunchbase API
        Crunchbase = @{
            Enabled = $true
            APIKey = $env:CRUNCHBASE_API_KEY
            BaseURL = "https://api.crunchbase.com/api/v4"
            RateLimit = 200
            Timeout = 30000
        }
        
        # News API
        NewsAPI = @{
            Enabled = $true
            APIKey = $env:NEWS_API_KEY
            BaseURL = "https://newsapi.org/v2"
            RateLimit = 1000
            Timeout = 15000
        }
        
        # OpenAI API (for AI analysis)
        OpenAI = @{
            Enabled = $true
            APIKey = $env:OPENAI_API_KEY
            Model = "gpt-4"
            MaxTokens = 4000
            Temperature = 0.7
        }
        
        # SEC EDGAR API
        SECEDGAR = @{
            Enabled = $true
            BaseURL = "https://www.sec.gov/cgi-bin/browse-edgar"
            UserAgent = "Clearglassinc Intelligence Bot contact@clearglassinc.com"
            RateLimit = 10
        }
        
        # Clearglassinc Cloud API
        ClearglassincCloud = @{
            Enabled = $false
            APIKey = $env:CLEARGLASSINC_API_KEY
            BaseURL = "https://api.clearglassinc.com/v2"
            Timeout = 30000
        }
    }
    
    # Data Collection Settings
    DataCollection = @{
        CacheEnabled = $true
        CacheTimeout = 3600  # seconds
        MaxConcurrentRequests = 10
        RequestDelay = 2000  # milliseconds between requests
        RetryAttempts = 3
        RetryDelay = 5000
        UserAgent = "Clearglassinc-Intelligence-Bot/2.0"
    }
    
    # Database Configuration
    Database = @{
        Type = "SQLite"  # SQLite, PostgreSQL, MySQL, MSSQL
        Path = ".\data\aerospace_intel.db"
        ConnectionString = ""
        AutoBackup = $true
        BackupInterval = 86400  # daily
        RetentionDays = 90
    }
    
    # Scraping Targets
    ScrapingTargets = @{
        Industries = @(
            "Aerospace",
            "Defense",
            "Space Technology",
            "Satellite Communications",
            "Launch Services",
            "Aviation"
        )
        
        CompanyTypes = @(
            "Manufacturer",
            "Service Provider",
            "Technology Developer",
            "Research Organization"
        )
        
        DataPoints = @(
            "Company Profile",
            "Financial Data",
            "Leadership",
            "Products/Services",
            "News & Events",
            "Social Media",
            "Job Postings",
            "Patents",
            "Partnerships",
            "Competitors"
        )
    }
    
    # Analysis Settings
    Analysis = @{
        EnableAI = $true
        EnableSentimentAnalysis = $true
        EnableCompetitiveIntelligence = $true
        EnablePredictiveModeling = $true
        
        ScoringWeights = @{
            MarketPosition = 0.25
            FinancialHealth = 0.20
            Innovation = 0.25
            GrowthPotential = 0.20
            RiskAssessment = 0.10
        }
        
        RiskFactors = @(
            "Technical",
            "Market",
            "Financial",
            "Regulatory",
            "Competitive",
            "Operational"
        )
    }
    
    # Predictive Modeling
    PredictiveModeling = @{
        Enabled = $true
        ModelPath = ".\models\aerospace_predictor.pkl"
        DefaultTimeframe = 30  # days
        ConfidenceThreshold = 0.75
        
        Algorithms = @(
            "Time Series Analysis",
            "Regression Models",
            "Neural Networks",
            "Ensemble Methods"
        )
        
        PredictionTargets = @(
            "Market Growth",
            "Company Performance",
            "Investment Opportunities",
            "Technology Trends",
            "Competitive Dynamics"
        )
    }
    
    # Reporting Configuration
    Reporting = @{
        DefaultFormat = "HTML"
        SupportedFormats = @("HTML", "PDF", "JSON", "Excel", "Markdown")
        IncludeVisualizations = $true
        IncludeExecutiveSummary = $true
        IncludeRawData = $false
        
        BrandingColors = @{
            Primary = "#667eea"
            Secondary = "#764ba2"
            Accent = "#f093fb"
            Background = "#f5f5f5"
        }
    }
    
    # Cloud Integration
    CloudIntegration = @{
        Enabled = $false
        Provider = "Azure"  # Azure, AWS, GCP
        StorageAccount = ""
        Region = "eastus"
        
        Features = @{
            AutoUpload = $false
            RealTimeSync = $false
            DistributedProcessing = $false
        }
    }
    
    # Monitoring & Alerts
    Monitoring = @{
        Enabled = $true
        CheckInterval = 300  # seconds
        
        Alerts = @{
            Email = @{
                Enabled = $false
                Recipients = @()
                SMTPServer = ""
            }
            
            Webhook = @{
                Enabled = $false
                URL = ""
            }
            
            Slack = @{
                Enabled = $false
                WebhookURL = ""
            }
        }
        
        TriggerConditions = @(
            "Major news event",
            "Funding announcement",
            "Leadership change",
            "Significant price movement",
            "Competitive threat"
        )
    }
    
    # Logging Configuration
    Logging = @{
        Enabled = $true
        LogPath = ".\data\logs"
        LogLevel = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
        MaxLogSize = 10485760  # 10MB
        LogRetentionDays = 30
        IncludeTimestamp = $true
        IncludeLevel = $true
        IncludeSource = $true
    }
    
    # Security Settings
    Security = @{
        EncryptCache = $false
        EncryptDatabase = $false
        RequireAPIKeys = $true
        RateLimitEnforcement = $true
        
        DataPrivacy = @{
            AnonymizePersonalInfo = $true
            DataRetentionDays = 365
            ComplianceMode = "GDPR"  # GDPR, CCPA, BOTH
        }
    }
    
    # Performance Optimization
    Performance = @{
        EnableCaching = $true
        EnableParallelProcessing = $true
        MaxThreads = 8
        MemoryLimit = 2048  # MB
        EnableGarbageCollection = $true
    }
    
    # Experimental Features
    Experimental = @{
        AIAssisted Scraping = $false
        BlockchainVerification = $false
        QuantumResistantEncryption = $false
        EdgeComputing = $false
    }
    
    # License Information
    License = @{
        Type = "Commercial"
        Owner = "Clearglassinc"
        ExpirationDate = "2030-12-31"
        MaxUsers = 100
        MaxDevices = 50
        FeatureLevel = "Enterprise"
    }
}
