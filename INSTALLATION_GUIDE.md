# Clearglassinc Aerospace Intelligence System
## Version 2.0.0 - Installation & Quick Start Guide

---

## 🚀 Overview

The **Clearglassinc Aerospace Intelligence System** is an enterprise-grade platform for aerospace market intelligence, combining multi-source data scraping, machine learning predictions, and comprehensive analytics.

### Key Features
- ✅ Multi-source data aggregation (LinkedIn, Crunchbase, SEC, Patents)
- ✅ Predictive analytics powered by ensemble ML models
- ✅ Real-time company metrics tracking
- ✅ REST API with OpenAPI 3.0 specification
- ✅ Enterprise SQL Server database
- ✅ Scalable architecture for 2026-2030 deployment

---

## 📋 System Requirements

### Minimum Requirements
- **OS:** Windows Server 2022+ or Windows 11 Pro/Enterprise
- **RAM:** 8GB (16GB recommended)
- **Storage:** 100GB (for database and logs)
- **CPU:** 4 cores (8+ cores recommended)

### Software Prerequisites
- **PowerShell:** 7.4 or later
- **Python:** 3.11 or later
- **SQL Server:** 2022 (Express, Standard, or Enterprise)
- **Node.js:** 20+ (optional, for API server)

---

## 📦 Installation Steps

### Step 1: Install SQL Server

1. Download SQL Server 2022 from [Microsoft Download Center](https://www.microsoft.com/en-us/sql-server/sql-server-downloads)
2. Install SQL Server with default settings
3. Install SQL Server Management Studio (SSMS) for database management

### Step 2: Create Database

1. Open SSMS and connect to your SQL Server instance
2. Open the `database_schema.sql` file
3. Execute the script to create the `AerospaceIntel` database
4. Verify creation:
   ```sql
   SELECT name FROM sys.databases WHERE name = 'AerospaceIntel'
   ```

### Step 3: Install Python Dependencies

```bash
# Install required packages
pip install numpy pandas scikit-learn xgboost prophet tensorflow requests beautifulsoup4 lxml pyodbc
```

Verify installation:
```bash
python -c "import sklearn, xgboost, prophet; print('Dependencies installed successfully')"
```

### Step 4: Configure PowerShell Module

1. Copy `AerospaceIntel.psm1` to your PowerShell modules directory:
   ```powershell
   $modulePath = "$env:USERPROFILE\Documents\PowerShell\Modules\AerospaceIntel"
   New-Item -ItemType Directory -Force -Path $modulePath
   Copy-Item AerospaceIntel.psm1 $modulePath\
   ```

2. Import the module:
   ```powershell
   Import-Module AerospaceIntel
   ```

### Step 5: Set Environment Variables

```powershell
# Database connection
$env:CLEARGLASSINC_DB = "Server=localhost;Database=AerospaceIntel;Integrated Security=true"

# API keys (obtain from respective providers)
$env:CRUNCHBASE_API_KEY = "your-crunchbase-api-key"

# API endpoint (if using hosted version)
$env:CLEARGLASSINC_API = "https://api.clearglassinc.com/v2"
```

Make these permanent by adding to your PowerShell profile:
```powershell
notepad $PROFILE
# Add the above environment variable commands
```

---

## ⚡ Quick Start

### Example 1: Scrape Company Data

```powershell
# Import module
Import-Module AerospaceIntel

# Scrape LinkedIn data for Firefly Aerospace
$company = Get-LinkedInCompanyData -CompanyUrl "https://www.linkedin.com/company/firefly-space-systems/"

# View company details
$company | Format-List

# Aggregate data from multiple sources
$fullData = Get-AggregatedCompanyData -CompanyName "Firefly Aerospace" `
    -IncludeSources @('LinkedIn', 'Crunchbase', 'SEC_Edgar', 'SpaceNews')
```

### Example 2: Generate Predictions

```powershell
# Run growth trajectory prediction
$prediction = Invoke-PredictiveAnalysis `
    -CompanyId $company.CompanyId `
    -PredictionType GrowthTrajectory

# View prediction results
$prediction.Predictions | ConvertTo-Json -Depth 5

# Run funding probability prediction
$fundingPred = Invoke-PredictiveAnalysis `
    -CompanyId $company.CompanyId `
    -PredictionType FundingProbability

Write-Host "Funding Probability: $($fundingPred.Predictions.funding_probability_6months * 100)%"
```

### Example 3: Generate Reports

```powershell
# Export comprehensive Excel report
$reportPath = Export-AerospaceIntelReport `
    -CompanyIds @($company.CompanyId) `
    -OutputFormat Excel `
    -IncludePredictions

Write-Host "Report generated: $reportPath"

# Export JSON data
$jsonPath = Export-AerospaceIntelReport `
    -CompanyIds @($company.CompanyId) `
    -OutputFormat JSON

# View JSON output
Get-Content $jsonPath | ConvertFrom-Json | Format-List
```

### Example 4: Batch Processing

```powershell
# Scrape multiple companies
$companies = @(
    "https://www.linkedin.com/company/firefly-space-systems/",
    "https://www.linkedin.com/company/rocket-lab/",
    "https://www.linkedin.com/company/relativity-space/"
)

$scrapedCompanies = $companies | ForEach-Object {
    Get-LinkedInCompanyData -CompanyUrl $_ -Verbose
}

# Generate predictions for all companies
$predictions = $scrapedCompanies | ForEach-Object {
    Invoke-PredictiveAnalysis -CompanyId $_.CompanyId -PredictionType Innovation
}

# Export consolidated report
Export-AerospaceIntelReport `
    -CompanyIds $scrapedCompanies.CompanyId `
    -OutputFormat Excel `
    -IncludePredictions
```

---

## 🔧 Configuration

### Database Connection Strings

**Local SQL Server (Windows Authentication):**
```
Server=localhost;Database=AerospaceIntel;Integrated Security=true
```

**SQL Server with credentials:**
```
Server=localhost;Database=AerospaceIntel;User Id=sa;Password=YourPassword
```

**Remote SQL Server:**
```
Server=your-server.database.windows.net;Database=AerospaceIntel;User Id=admin;Password=YourPassword
```

### API Rate Limiting

Configure rate limits in the module:
```powershell
$script:Config.RateLimitPerMinute = 100  # Adjust based on your needs
$script:Config.MaxConcurrentRequests = 10
```

### Caching

Enable/disable caching:
```powershell
$script:Config.CacheTimeout = 3600  # 1 hour in seconds
# Set to 0 to disable caching
```

---

## 🔌 API Usage

### Starting the API Server

```bash
# If using Node.js API server
npm install
npm start

# API will be available at http://localhost:8080/v2
```

### Example API Calls

**Get all companies:**
```bash
curl -X GET "https://api.clearglassinc.com/v2/companies" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Trigger scraping:**
```bash
curl -X POST "https://api.clearglassinc.com/v2/companies/{companyId}/scrape" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sources": ["LinkedIn", "Crunchbase"]}'
```

**Generate prediction:**
```bash
curl -X POST "https://api.clearglassinc.com/v2/predictions" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "companyId": "uuid-here",
    "predictionType": "GrowthTrajectory",
    "horizon": 365
  }'
```

---

## 📊 Database Schema

### Core Tables
- `AerospaceCompanies` - Master company registry
- `CompanyMetrics` - Time series metrics
- `FundingRounds` - Funding history
- `Patents` - Patent filings and grants
- `NewsArticles` - News and sentiment data
- `CompanyPredictions` - ML prediction results

### Useful Queries

**Get top growing companies:**
```sql
EXEC sp_GetTopGrowingCompanies @TopN = 10, @DaysBack = 90
```

**Company with latest metrics:**
```sql
EXEC sp_GetCompanyWithMetrics @CompanyId = 'your-company-id'
```

**Innovation score:**
```sql
SELECT dbo.fn_CalculateInnovationScore('your-company-id') AS InnovationScore
```

---

## 🐍 Python ML Engine

### Standalone Usage

```bash
# Create input JSON
cat > input.json <<EOF
{
  "company_id": "uuid-here",
  "prediction_type": "GrowthTrajectory",
  "historical_data": [
    {
      "MetricDate": "2025-01-01",
      "EmployeeGrowthRate": 0.05,
      "EstimatedRevenue": 10000000
    }
  ]
}
EOF

# Run prediction
python ml_engine.py --input input.json --output json
```

### Customizing Models

Edit `ml_engine.py` to adjust model parameters:

```python
# Adjust Random Forest parameters
self.models['random_forest'] = RandomForestRegressor(
    n_estimators=200,  # Increase for better accuracy
    max_depth=10,
    random_state=42
)

# Adjust ensemble weights
self.ensemble_weights = {
    'random_forest': 0.4,
    'xgboost': 0.35,
    'gradient_boost': 0.25
}
```

---

## 🚨 Troubleshooting

### Common Issues

**Issue: "Cannot connect to database"**
```powershell
# Test SQL connection
Test-Connection -ComputerName localhost -Port 1433

# Verify SQL Server is running
Get-Service -Name MSSQLSERVER

# Check connection string
$env:CLEARGLASSINC_DB
```

**Issue: "Python module not found"**
```bash
# Reinstall dependencies
pip install --upgrade --force-reinstall numpy pandas scikit-learn xgboost

# Verify Python version
python --version  # Should be 3.11+
```

**Issue: "Rate limit exceeded"**
```powershell
# Increase delay between requests
$script:Config.RateLimitPerMinute = 30  # Reduce requests per minute
```

**Issue: "LinkedIn scraping fails"**
- LinkedIn requires authentication for most data
- Consider using LinkedIn API with official credentials
- Implement proper User-Agent headers and rate limiting

---

## 📈 Performance Optimization

### Database Indexing

```sql
-- Add custom indexes for frequently queried columns
CREATE INDEX IX_CompanyMetrics_Sentiment ON CompanyMetrics(MarketSentiment)
CREATE INDEX IX_Patents_Classification ON Patents(Classifications)
```

### Caching Strategy

```powershell
# Enable Redis caching (requires Redis installation)
$script:Config.UseRedisCache = $true
$script:Config.RedisConnection = "localhost:6379"
```

### Parallel Processing

```powershell
# Process companies in parallel
$companies | ForEach-Object -Parallel {
    Get-AggregatedCompanyData -CompanyName $_.Name
} -ThrottleLimit 5
```

---

## 🔒 Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **Database Credentials**: Use Windows Authentication when possible
3. **API Access**: Implement JWT authentication with short expiry
4. **Rate Limiting**: Prevent abuse with per-user rate limits
5. **Input Validation**: Sanitize all user inputs before database queries
6. **Logging**: Enable audit logging for compliance

---

## 📚 Additional Resources

- **Full Documentation**: `Clearglassinc_Complete_Documentation.docx`
- **API Specification**: `api_specification.yaml` (OpenAPI 3.0)
- **Database Schema**: `database_schema.sql`
- **Python ML Engine**: `ml_engine.py`
- **PowerShell Module**: `AerospaceIntel.psm1`

---

## 🆘 Support

For commercial licensing, enterprise support, or custom development:

**Clearglassinc**
- Email: support@clearglassinc.com
- Sales: sales@clearglassinc.com
- Website: https://www.clearglassinc.com

---

## 📄 License

**Proprietary Software**

Copyright © 2026 Clearglassinc. All Rights Reserved.

This software is licensed for commercial use only. Redistribution, modification, or use without explicit written permission from Clearglassinc is prohibited.

---

## 🎯 Next Steps

1. ✅ Complete installation steps above
2. ✅ Run the Quick Start examples
3. ✅ Configure API keys for data sources
4. ✅ Customize scraping sources for your needs
5. ✅ Set up scheduled jobs for automated data collection
6. ✅ Integrate with your existing BI tools
7. ✅ Deploy to production environment

**Ready to revolutionize aerospace intelligence!** 🚀

---

*Built with precision for 2026-2030 scale by Clearglassinc*
