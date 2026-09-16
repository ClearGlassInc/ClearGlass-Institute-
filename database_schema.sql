-- ============================================================================
-- Clearglassinc Aerospace Intelligence Database Schema
-- Version: 2.0.0
-- Database: SQL Server 2022+
-- Copyright (c) 2026 Clearglassinc. All Rights Reserved.
-- ============================================================================

-- Drop existing database if exists (CAUTION: Production use)
-- DROP DATABASE IF EXISTS AerospaceIntel;

CREATE DATABASE AerospaceIntel;
GO

USE AerospaceIntel;
GO

-- ============================================================================
-- CORE TABLES
-- ============================================================================

-- Companies Master Table
CREATE TABLE AerospaceCompanies (
    CompanyId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Name NVARCHAR(255) NOT NULL,
    LinkedInUrl NVARCHAR(500),
    Website NVARCHAR(500),
    Industry NVARCHAR(100),
    Headquarters NVARCHAR(255),
    EmployeeCount INT,
    CompanyType NVARCHAR(50), -- Startup, Established, Government, etc.
    Founded DATE,
    FundingStage NVARCHAR(50), -- Seed, Series A-F, IPO, etc.
    LastFundingRound DECIMAL(18,2),
    LastFundingDate DATE,
    TotalFunding DECIMAL(18,2),
    Valuation DECIMAL(18,2),
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    LastUpdated DATETIME2 DEFAULT GETDATE(),
    LastScrapedAt DATETIME2,
    
    INDEX IX_CompanyName (Name),
    INDEX IX_CompanyIndustry (Industry),
    INDEX IX_CompanyActive (IsActive),
    INDEX IX_LastUpdated (LastUpdated)
);

-- Company Specialties (Many-to-Many)
CREATE TABLE CompanySpecialties (
    SpecialtyId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    Specialty NVARCHAR(100) NOT NULL,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_CompanySpecialty (CompanyId, Specialty)
);

-- Company Metrics Time Series
CREATE TABLE CompanyMetrics (
    MetricId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    MetricDate DATE NOT NULL,
    EmployeeCount INT,
    EmployeeGrowthRate DECIMAL(10,4), -- Percentage growth
    EstimatedRevenue DECIMAL(18,2),
    RevenueGrowthRate DECIMAL(10,4),
    JobPostings INT,
    PatentFilings INT,
    NewsArticles INT,
    SocialMediaEngagement BIGINT,
    LinkedInFollowers INT,
    TwitterFollowers INT,
    MarketSentiment DECIMAL(5,4), -- -1.0 to 1.0
    WebTraffic BIGINT,
    AppDownloads BIGINT,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_CompanyMetricsDate (CompanyId, MetricDate DESC),
    INDEX IX_MetricDate (MetricDate)
);

-- ============================================================================
-- FUNDING AND FINANCIAL DATA
-- ============================================================================

CREATE TABLE FundingRounds (
    RoundId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    RoundType NVARCHAR(50), -- Seed, Series A, Series B, etc.
    Amount DECIMAL(18,2),
    Currency NVARCHAR(3) DEFAULT 'USD',
    AnnouncedDate DATE,
    ClosedDate DATE,
    LeadInvestor NVARCHAR(255),
    Valuation DECIMAL(18,2),
    PostMoneyValuation DECIMAL(18,2),
    NumberOfInvestors INT,
    SourceUrl NVARCHAR(500),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_FundingCompany (CompanyId),
    INDEX IX_FundingDate (AnnouncedDate)
);

CREATE TABLE Investors (
    InvestorId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    InvestorName NVARCHAR(255) NOT NULL,
    InvestorType NVARCHAR(50), -- VC, Angel, Corporate, Government
    Website NVARCHAR(500),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    INDEX IX_InvestorName (InvestorName)
);

CREATE TABLE CompanyInvestors (
    CompanyInvestorId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    InvestorId UNIQUEIDENTIFIER NOT NULL,
    RoundId UNIQUEIDENTIFIER,
    InvestmentDate DATE,
    InvestmentAmount DECIMAL(18,2),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    FOREIGN KEY (InvestorId) REFERENCES Investors(InvestorId),
    FOREIGN KEY (RoundId) REFERENCES FundingRounds(RoundId),
    INDEX IX_CompanyInvestor (CompanyId, InvestorId)
);

-- ============================================================================
-- PATENTS AND INNOVATION
-- ============================================================================

CREATE TABLE Patents (
    PatentId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    PatentNumber NVARCHAR(50) NOT NULL,
    Title NVARCHAR(500),
    Abstract NVARCHAR(MAX),
    FilingDate DATE,
    GrantDate DATE,
    PatentOffice NVARCHAR(10), -- USPTO, EPO, etc.
    Status NVARCHAR(50), -- Pending, Granted, Expired
    Inventors NVARCHAR(MAX), -- JSON array of inventor names
    Classifications NVARCHAR(MAX), -- JSON array of IPC classifications
    Citations INT,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_PatentCompany (CompanyId),
    INDEX IX_PatentNumber (PatentNumber),
    INDEX IX_PatentDate (FilingDate)
);

-- ============================================================================
-- NEWS AND SOCIAL MEDIA
-- ============================================================================

CREATE TABLE NewsArticles (
    ArticleId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    Title NVARCHAR(500) NOT NULL,
    Url NVARCHAR(1000),
    Source NVARCHAR(100),
    PublishedDate DATETIME2,
    Content NVARCHAR(MAX),
    Sentiment DECIMAL(5,4), -- -1.0 to 1.0
    Category NVARCHAR(100), -- Funding, Product Launch, Partnership, etc.
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_NewsCompany (CompanyId),
    INDEX IX_NewsDate (PublishedDate DESC),
    INDEX IX_NewsSentiment (Sentiment)
);

CREATE TABLE SocialMediaPosts (
    PostId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    Platform NVARCHAR(50), -- LinkedIn, Twitter, etc.
    PostUrl NVARCHAR(1000),
    Content NVARCHAR(MAX),
    PostedDate DATETIME2,
    Likes INT,
    Shares INT,
    Comments INT,
    Engagement INT AS (Likes + Shares + Comments * 2) PERSISTED,
    Sentiment DECIMAL(5,4),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_SocialCompany (CompanyId),
    INDEX IX_SocialDate (PostedDate DESC)
);

-- ============================================================================
-- LEADERSHIP AND KEY PEOPLE
-- ============================================================================

CREATE TABLE CompanyLeadership (
    LeadershipId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    PersonName NVARCHAR(255) NOT NULL,
    Title NVARCHAR(100),
    LinkedInUrl NVARCHAR(500),
    StartDate DATE,
    EndDate DATE,
    IsCurrent BIT DEFAULT 1,
    Biography NVARCHAR(MAX),
    Education NVARCHAR(MAX), -- JSON
    PreviousRoles NVARCHAR(MAX), -- JSON
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    INDEX IX_LeadershipCompany (CompanyId),
    INDEX IX_LeadershipCurrent (CompanyId, IsCurrent)
);

-- ============================================================================
-- PREDICTIONS AND ML MODELS
-- ============================================================================

CREATE TABLE PredictionModels (
    ModelId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    ModelName NVARCHAR(100) NOT NULL,
    ModelType NVARCHAR(50), -- GrowthTrajectory, FundingProbability, etc.
    Version NVARCHAR(20),
    TrainedDate DATETIME2,
    Accuracy DECIMAL(5,4),
    Parameters NVARCHAR(MAX), -- JSON
    IsActive BIT DEFAULT 1,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    INDEX IX_ModelType (ModelType, IsActive)
);

CREATE TABLE CompanyPredictions (
    PredictionId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    CompanyId UNIQUEIDENTIFIER NOT NULL,
    ModelId UNIQUEIDENTIFIER NOT NULL,
    PredictionType NVARCHAR(50),
    PredictionDate DATETIME2 NOT NULL,
    PredictionHorizon INT, -- Days into future
    Confidence DECIMAL(5,4),
    Predictions NVARCHAR(MAX), -- JSON with all prediction details
    ActualOutcome NVARCHAR(MAX), -- JSON with actual results (for validation)
    IsValidated BIT DEFAULT 0,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE CASCADE,
    FOREIGN KEY (ModelId) REFERENCES PredictionModels(ModelId),
    INDEX IX_PredictionCompany (CompanyId),
    INDEX IX_PredictionDate (PredictionDate DESC),
    INDEX IX_PredictionType (PredictionType)
);

-- ============================================================================
-- DATA SOURCES AND SCRAPING LOGS
-- ============================================================================

CREATE TABLE DataSources (
    SourceId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    SourceName NVARCHAR(100) NOT NULL,
    SourceType NVARCHAR(50), -- LinkedIn, Crunchbase, SEC, etc.
    BaseUrl NVARCHAR(500),
    ApiKey NVARCHAR(255), -- Encrypted
    IsActive BIT DEFAULT 1,
    RateLimitPerMinute INT,
    LastAccessedAt DATETIME2,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    INDEX IX_SourceName (SourceName)
);

CREATE TABLE ScrapingLogs (
    LogId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    SourceId UNIQUEIDENTIFIER NOT NULL,
    CompanyId UNIQUEIDENTIFIER,
    ScrapeType NVARCHAR(50),
    StartTime DATETIME2 NOT NULL,
    EndTime DATETIME2,
    Status NVARCHAR(50), -- Success, Failed, Partial
    RecordsScraped INT,
    ErrorMessage NVARCHAR(MAX),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (SourceId) REFERENCES DataSources(SourceId),
    FOREIGN KEY (CompanyId) REFERENCES AerospaceCompanies(CompanyId) ON DELETE SET NULL,
    INDEX IX_ScrapeStatus (Status, StartTime DESC),
    INDEX IX_ScrapeCompany (CompanyId)
);

-- ============================================================================
-- USER AND SYSTEM TABLES
-- ============================================================================

CREATE TABLE SystemUsers (
    UserId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    Username NVARCHAR(100) NOT NULL,
    Email NVARCHAR(255) NOT NULL,
    PasswordHash NVARCHAR(255),
    Role NVARCHAR(50), -- Admin, Analyst, Viewer
    IsActive BIT DEFAULT 1,
    LastLoginAt DATETIME2,
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    UNIQUE (Username),
    UNIQUE (Email),
    INDEX IX_UserRole (Role, IsActive)
);

CREATE TABLE AuditLog (
    AuditId UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    UserId UNIQUEIDENTIFIER,
    Action NVARCHAR(100),
    TableName NVARCHAR(100),
    RecordId UNIQUEIDENTIFIER,
    OldValues NVARCHAR(MAX), -- JSON
    NewValues NVARCHAR(MAX), -- JSON
    IPAddress NVARCHAR(45),
    CreatedAt DATETIME2 DEFAULT GETDATE(),
    
    FOREIGN KEY (UserId) REFERENCES SystemUsers(UserId) ON DELETE SET NULL,
    INDEX IX_AuditUser (UserId),
    INDEX IX_AuditDate (CreatedAt DESC)
);

-- ============================================================================
-- STORED PROCEDURES
-- ============================================================================

-- Get Company with Latest Metrics
GO
CREATE PROCEDURE sp_GetCompanyWithMetrics
    @CompanyId UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        c.*,
        cs.Specialty,
        m.MetricDate,
        m.EmployeeGrowthRate,
        m.EstimatedRevenue,
        m.MarketSentiment
    FROM AerospaceCompanies c
    LEFT JOIN CompanySpecialties cs ON c.CompanyId = cs.CompanyId
    LEFT JOIN (
        SELECT *
        FROM CompanyMetrics
        WHERE MetricDate = (SELECT MAX(MetricDate) FROM CompanyMetrics WHERE CompanyId = @CompanyId)
    ) m ON c.CompanyId = m.CompanyId
    WHERE c.CompanyId = @CompanyId;
END
GO

-- Get Top Growing Companies
GO
CREATE PROCEDURE sp_GetTopGrowingCompanies
    @TopN INT = 10,
    @DaysBack INT = 90
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT TOP (@TopN)
        c.CompanyId,
        c.Name,
        c.Industry,
        c.EmployeeCount,
        AVG(m.EmployeeGrowthRate) AS AvgGrowthRate,
        MAX(m.MetricDate) AS LatestMetric
    FROM AerospaceCompanies c
    INNER JOIN CompanyMetrics m ON c.CompanyId = m.CompanyId
    WHERE m.MetricDate >= DATEADD(day, -@DaysBack, GETDATE())
        AND c.IsActive = 1
    GROUP BY c.CompanyId, c.Name, c.Industry, c.EmployeeCount
    ORDER BY AvgGrowthRate DESC;
END
GO

-- Get Company Predictions
GO
CREATE PROCEDURE sp_GetCompanyPredictions
    @CompanyId UNIQUEIDENTIFIER,
    @PredictionType NVARCHAR(50) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SELECT 
        p.*,
        m.ModelName,
        m.Version AS ModelVersion,
        m.Accuracy AS ModelAccuracy
    FROM CompanyPredictions p
    INNER JOIN PredictionModels m ON p.ModelId = m.ModelId
    WHERE p.CompanyId = @CompanyId
        AND (@PredictionType IS NULL OR p.PredictionType = @PredictionType)
    ORDER BY p.PredictionDate DESC;
END
GO

-- ============================================================================
-- VIEWS
-- ============================================================================

-- Company Summary View
GO
CREATE VIEW vw_CompanySummary AS
SELECT 
    c.CompanyId,
    c.Name,
    c.Industry,
    c.Headquarters,
    c.EmployeeCount,
    c.FundingStage,
    c.TotalFunding,
    c.Valuation,
    COUNT(DISTINCT f.RoundId) AS FundingRounds,
    COUNT(DISTINCT p.PatentId) AS Patents,
    COUNT(DISTINCT n.ArticleId) AS NewsArticles,
    MAX(m.MetricDate) AS LatestMetricDate,
    (SELECT TOP 1 MarketSentiment FROM CompanyMetrics WHERE CompanyId = c.CompanyId ORDER BY MetricDate DESC) AS CurrentSentiment
FROM AerospaceCompanies c
LEFT JOIN FundingRounds f ON c.CompanyId = f.CompanyId
LEFT JOIN Patents p ON c.CompanyId = p.CompanyId
LEFT JOIN NewsArticles n ON c.CompanyId = n.CompanyId
LEFT JOIN CompanyMetrics m ON c.CompanyId = m.CompanyId
WHERE c.IsActive = 1
GROUP BY 
    c.CompanyId, c.Name, c.Industry, c.Headquarters, 
    c.EmployeeCount, c.FundingStage, c.TotalFunding, c.Valuation;
GO

-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Calculate Company Innovation Score
GO
CREATE FUNCTION fn_CalculateInnovationScore(@CompanyId UNIQUEIDENTIFIER)
RETURNS DECIMAL(5,2)
AS
BEGIN
    DECLARE @Score DECIMAL(5,2);
    DECLARE @PatentCount INT;
    DECLARE @EmployeeCount INT;
    DECLARE @NewsCount INT;
    DECLARE @AvgSentiment DECIMAL(5,4);
    
    SELECT @PatentCount = COUNT(*) FROM Patents WHERE CompanyId = @CompanyId;
    SELECT @EmployeeCount = EmployeeCount FROM AerospaceCompanies WHERE CompanyId = @CompanyId;
    SELECT @NewsCount = COUNT(*) FROM NewsArticles WHERE CompanyId = @CompanyId AND PublishedDate >= DATEADD(year, -1, GETDATE());
    SELECT @AvgSentiment = AVG(Sentiment) FROM NewsArticles WHERE CompanyId = @CompanyId AND PublishedDate >= DATEADD(year, -1, GETDATE());
    
    SET @Score = (
        (@PatentCount * 1.0 / NULLIF(@EmployeeCount, 0) * 1000 * 30) +  -- Patents per employee (30%)
        (@NewsCount * 0.5) +  -- News coverage (20%)
        ((@AvgSentiment + 1) * 25)  -- Sentiment (50%, scaled from -1,1 to 0,50)
    );
    
    RETURN ISNULL(@Score, 0);
END
GO

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update LastUpdated timestamp
GO
CREATE TRIGGER tr_UpdateCompanyTimestamp
ON AerospaceCompanies
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE AerospaceCompanies
    SET LastUpdated = GETDATE()
    WHERE CompanyId IN (SELECT CompanyId FROM inserted);
END
GO

-- ============================================================================
-- SEED DATA
-- ============================================================================

-- Insert Firefly Aerospace
INSERT INTO AerospaceCompanies (Name, LinkedInUrl, Website, Industry, Headquarters, EmployeeCount, CompanyType, FundingStage)
VALUES (
    'Firefly Aerospace',
    'https://www.linkedin.com/company/firefly-space-systems/',
    'http://www.fireflyspace.com',
    'Aviation & Aerospace',
    'Cedar Park, Texas',
    750,
    'Privately Held',
    'Series C'
);

DECLARE @FireflyId UNIQUEIDENTIFIER = (SELECT CompanyId FROM AerospaceCompanies WHERE Name = 'Firefly Aerospace');

INSERT INTO CompanySpecialties (CompanyId, Specialty)
VALUES 
    (@FireflyId, 'Newspace'),
    (@FireflyId, 'Aerospace'),
    (@FireflyId, 'Engineering'),
    (@FireflyId, 'Launch Vehicle'),
    (@FireflyId, 'Spacecraft'),
    (@FireflyId, 'lunar'),
    (@FireflyId, 'Space Investment'),
    (@FireflyId, 'Venture Capital');

-- Insert sample data source
INSERT INTO DataSources (SourceName, SourceType, BaseUrl, RateLimitPerMinute, IsActive)
VALUES 
    ('LinkedIn', 'Social', 'https://www.linkedin.com', 30, 1),
    ('Crunchbase', 'Financial', 'https://www.crunchbase.com', 60, 1),
    ('SEC EDGAR', 'Financial', 'https://www.sec.gov', 10, 1),
    ('SpaceNews', 'News', 'https://spacenews.com', 30, 1);

PRINT 'Database schema created successfully for Clearglassinc Aerospace Intelligence System v2.0';
GO
