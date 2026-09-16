# CLEARGLASSINC AEROSPACE INTELLIGENCE SYSTEM
## Quick Start Guide

---

**Get up and running in 15 minutes!**

---

## ⚡ RAPID SETUP

### 1. System Check (2 minutes)

Verify you have:

```powershell
# Check PowerShell version (need 7.0+)
$PSVersionTable

# Should show: PSVersion 7.x.x or higher
```

If you don't have PowerShell 7+:
- **Windows**: Download from https://github.com/PowerShell/PowerShell/releases
- **Mac**: `brew install powershell`
- **Linux**: Follow https://docs.microsoft.com/powershell/scripting/install/installing-powershell

---

### 2. Extract Files (1 minute)

```powershell
# Extract the package
Expand-Archive -Path "Clearglassinc-AerospaceIntel-v2.0.zip" -DestinationPath "C:\Clearglassinc\"

# Navigate to folder
cd C:\Clearglassinc\clearglassinc-aerospace-intel
```

---

### 3. Set License Key (1 minute)

```powershell
# Set your Clearglassinc license key (provided with purchase)
[System.Environment]::SetEnvironmentVariable('CLEARGLASSINC_API_KEY', 'YOUR-LICENSE-KEY-HERE', 'User')

# Restart PowerShell for changes to take effect
```

---

### 4. Run First Command (1 minute)

```powershell
# Test the system with a sample company
.\src\AerospaceIntel.ps1 -Mode Scrape -Company "Firefly Aerospace"
```

You should see:
```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║          CLEARGLASSINC AEROSPACE INTELLIGENCE SYSTEM         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝

[CLEARGLASSINC] Initializing Aerospace Intelligence System...
[CLEARGLASSINC] Scraping LinkedIn...
[CLEARGLASSINC] Scraping Crunchbase...
[CLEARGLASSINC] Operation completed successfully!
```

---

## 🚀 YOUR FIRST ANALYSIS (10 minutes)

### Step 1: Scrape Company Data

```powershell
.\src\AerospaceIntel.ps1 -Mode Scrape -Company "SpaceX"
```

**What this does**: Collects data from LinkedIn, Crunchbase, news APIs, company website

**Output**: Data saved to `.\data\cache\company_SpaceX_*.json`

---

### Step 2: Analyze the Company

```powershell
.\src\AerospaceIntel.ps1 -Mode Analyze -Company "SpaceX"
```

**What this does**: Runs AI analysis on collected data

**Output**: JSON with analysis results including:
- Competitive position
- Market opportunities  
- Risk assessment
- Growth potential
- Clearglassinc Score

---

### Step 3: Run Predictions

```powershell
.\src\AerospaceIntel.ps1 -Mode Predict -Timeframe 90
```

**What this does**: Forecasts market trends for next 90 days

**Output**: Predictions for:
- Market growth
- Investment trends
- Technology adoption
- Emerging companies

---

### Step 4: Generate Report

```powershell
.\src\AerospaceIntel.ps1 -Mode Report -Company "SpaceX" -OutputFormat "HTML"
```

**What this does**: Creates comprehensive HTML report

**Output**: Opens interactive report in your browser

**Report includes**:
- Executive summary
- Company analysis
- Predictions
- Visualizations
- Recommendations

---

## 🎯 COMMON COMMANDS

### Analyze Any Company

```powershell
.\src\AerospaceIntel.ps1 -Mode Scrape -Company "Rocket Lab"
.\src\AerospaceIntel.ps1 -Mode Analyze -Company "Rocket Lab"
.\src\AerospaceIntel.ps1 -Mode Report -Company "Rocket Lab"
```

### Monitor Company Real-Time

```powershell
# Continuously monitor (press Ctrl+C to stop)
.\src\AerospaceIntel.ps1 -Mode Monitor -Company "Blue Origin"
```

### Batch Process Multiple Companies

```powershell
# Create list of companies
$companies = @("SpaceX", "Blue Origin", "Rocket Lab", "Astra")

# Process each one
foreach ($company in $companies) {
    .\src\AerospaceIntel.ps1 -Mode Scrape -Company $company
    .\src\AerospaceIntel.ps1 -Mode Analyze -Company $company
}
```

### Generate PDF Report

```powershell
.\src\AerospaceIntel.ps1 -Mode Report -Company "SpaceX" -OutputFormat "PDF"
```

### Export to Excel

```powershell
.\src\AerospaceIntel.ps1 -Mode Report -Company "SpaceX" -OutputFormat "Excel"
```

---

## 🔑 OPTIONAL: API Keys

For enhanced features, add these API keys:

### LinkedIn API (Premium data)

```powershell
[System.Environment]::SetEnvironmentVariable('LINKEDIN_API_KEY', 'your-key-here', 'User')
```

**Get API key**: https://developer.linkedin.com  
**Cost**: $99/month  
**Benefit**: Employee data, growth metrics, detailed profiles

### Crunchbase API (Funding data)

```powershell
[System.Environment]::SetEnvironmentVariable('CRUNCHBASE_API_KEY', 'your-key-here', 'User')
```

**Get API key**: https://data.crunchbase.com  
**Cost**: $49-99/month  
**Benefit**: Funding rounds, investors, valuations

### News API (Media coverage)

```powershell
[System.Environment]::SetEnvironmentVariable('NEWS_API_KEY', 'your-key-here', 'User')
```

**Get API key**: https://newsapi.org  
**Cost**: Free tier available  
**Benefit**: News articles, sentiment analysis

### OpenAI API (AI insights)

```powershell
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'your-key-here', 'User')
```

**Get API key**: https://platform.openai.com  
**Cost**: Pay-as-you-go ($20-100/month typical)  
**Benefit**: Advanced AI analysis

**Note**: System works without these APIs but with limited data sources

---

## 📍 Where Are My Files?

### Data Cache
```
.\data\cache\
```
Raw scraped data in JSON format

### Reports
```
.\data\reports\
```
Generated HTML, PDF, Excel reports

### Logs
```
.\data\logs\
```
System logs for troubleshooting

### Configuration
```
.\config\config.psd1
```
Edit settings here

---

## ⚙️ CUSTOMIZE SETTINGS

Edit `.\config\config.psd1` to change:

**Data collection**:
```powershell
DataCollection = @{
    MaxConcurrentRequests = 10  # Increase for faster scraping
    RequestDelay = 2000         # Decrease carefully
}
```

**Database**:
```powershell
Database = @{
    Type = "SQLite"             # Or PostgreSQL, MySQL
    AutoBackup = $true          # Enable backups
}
```

**Reporting**:
```powershell
Reporting = @{
    DefaultFormat = "HTML"      # Or PDF, Excel, JSON
    IncludeVisualizations = $true
}
```

---

## 🆘 TROUBLESHOOTING

### Problem: "Execution of scripts is disabled"

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problem: "API key not found"

**Solution**:
```powershell
# Check if set
Get-ChildItem Env: | Where-Object { $_.Name -like "*API*" }

# Set if missing
[System.Environment]::SetEnvironmentVariable('CLEARGLASSINC_API_KEY', 'your-key', 'User')

# Restart PowerShell
```

### Problem: "Module not found"

**Solution**:
```powershell
# Verify you're in correct directory
cd C:\Clearglassinc\clearglassinc-aerospace-intel

# Check file exists
Test-Path .\src\AerospaceIntel.ps1
```

### Problem: "Rate limit exceeded"

**Solution**: In `config\config.psd1`, increase delays:
```powershell
DataCollection = @{
    RequestDelay = 5000         # 5 seconds
    MaxConcurrentRequests = 5   # Reduce concurrent requests
}
```

### Still having issues?

Check logs:
```powershell
Get-Content .\data\logs\aerospace_intel_*.log | Select-Object -Last 20
```

Or contact support: support@clearglassinc.com

---

## 📚 NEXT STEPS

### 1. Read Full Documentation

- **User Manual**: `.\docs\UserManual.md`
- **Installation Guide**: `.\docs\INSTALLATION.md`
- **API Reference**: `.\docs\APIReference.md`

### 2. Watch Video Tutorials

Available at: https://docs.clearglassinc.com/tutorials

Topics:
- System overview (10 min)
- Data collection (15 min)
- Analysis interpretation (20 min)
- Report customization (15 min)
- Advanced features (30 min)

### 3. Join Community

- **Forum**: https://community.clearglassinc.com
- **Slack**: clearglassinc.slack.com
- **Email**: support@clearglassinc.com

### 4. Schedule Training (Enterprise customers)

Email: training@clearglassinc.com

---

## 💡 PRO TIPS

### Tip 1: Use Verbose Mode

```powershell
.\src\AerospaceIntel.ps1 -Mode Analyze -Company "SpaceX" -Verbose
```

Get detailed progress information

### Tip 2: Save Time with Aliases

```powershell
# Create alias
Set-Alias ai "C:\Clearglassinc\clearglassinc-aerospace-intel\src\AerospaceIntel.ps1"

# Now use
ai -Mode Scrape -Company "SpaceX"
```

### Tip 3: Schedule Automatic Updates

```powershell
# Windows Task Scheduler
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-File C:\Clearglassinc\src\AerospaceIntel.ps1 -Mode Scrape -Company 'SpaceX'"
$trigger = New-ScheduledTaskTrigger -Daily -At "06:00AM"
Register-ScheduledTask -TaskName "Daily SpaceX Update" -Action $action -Trigger $trigger
```

### Tip 4: Backup Your Data

```powershell
# Backup data folder
Copy-Item -Path ".\data" -Destination ".\backup\data_$(Get-Date -Format 'yyyyMMdd')" -Recurse
```

### Tip 5: Export to Different Formats

```powershell
# Get data
$data = .\src\AerospaceIntel.ps1 -Mode Analyze -Company "SpaceX"

# Export as JSON
$data | ConvertTo-Json -Depth 10 | Out-File "spacex_analysis.json"

# Export as CSV (for specific sections)
$data.Analysis.CompetitivePosition | Export-Csv "competitors.csv"
```

---

## ✅ SUCCESS CHECKLIST

After completing this guide, you should be able to:

☑ Run the Clearglassinc system  
☑ Scrape company data  
☑ Analyze companies  
☑ Generate predictions  
☑ Create reports  
☑ Understand where files are stored  
☑ Troubleshoot common issues  

If you can do all these, you're ready for production use!

---

## 🎓 LEARNING PATH

### Week 1: Basics
- Run test commands
- Generate first report
- Explore output files

### Week 2: Intermediate
- Analyze 5-10 companies
- Customize configuration
- Batch processing

### Week 3: Advanced
- API integration
- Automated monitoring
- Custom reporting

### Week 4: Expert
- Advanced analytics
- Integration with other tools
- Team collaboration

---

## 📞 NEED HELP?

### Support Options

**Documentation**:
- User Manual: `.\docs\UserManual.md`
- Installation Guide: `.\docs\INSTALLATION.md`

**Community**:
- Forum: https://community.clearglassinc.com
- Slack: clearglassinc.slack.com

**Direct Support**:
- Email: support@clearglassinc.com
- Phone: +1 (555) 123-4567 (Enterprise customers)
- Portal: https://support.clearglassinc.com

**Response Times**:
- Critical: 4 hours
- High: 24 hours
- Normal: 48 hours

---

## 🚀 YOU'RE READY!

Congratulations! You now have a powerful aerospace intelligence platform at your fingertips.

**Start analyzing companies and making better decisions today.**

---

**© 2025 Clearglassinc. All rights reserved.**

Version 2.0.0 | Quick Start Guide
