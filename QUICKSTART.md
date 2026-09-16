# Clearglassinc Aerospace Intelligence System
# QUICK START GUIDE

## Version 5.0.0 - Commercial Product
© 2025-2030 Clearglassinc. All Rights Reserved.

═══════════════════════════════════════════════════════════════════

## 🚀 FASTEST WAY TO GET STARTED (5 Minutes)

### Step 1: Install Dependencies
```bash
pip install pandas numpy scikit-learn tensorflow beautifulsoup4 requests sqlalchemy openpyxl matplotlib plotly --break-system-packages
```

### Step 2: Initialize Database
```bash
cd scripts/python
python database_init.py
```

### Step 3: Run Your First Analysis
```powershell
cd scripts/powershell
.\ClearglassAerospace-Master.ps1 -Mode FullPipeline -CompanyFilter aerospace_defense -OutputFormat All -EnablePredictiveML
```

That's it! The system will:
✅ Collect aerospace market data from public APIs
✅ Analyze competitive landscape and sentiment
✅ Generate 5-year predictive forecasts
✅ Create Excel, PDF, and JSON reports

═══════════════════════════════════════════════════════════════════

## 📊 WHAT YOU GET

After running the system, find your outputs in:

**output/data/** - Raw collected market data
**output/reports/** - Excel and PDF analysis reports
**output/predictions/** - 5-year forecast files
**output/dashboards/** - Interactive visualizations

═══════════════════════════════════════════════════════════════════

## 🎯 COMMON COMMANDS

### Full Market Analysis (Recommended First Run)
```powershell
.\ClearglassAerospace-Master.ps1 -Mode FullPipeline -CompanyFilter all -OutputFormat All -EnablePredictiveML
```

### Quick Data Collection Only
```powershell
.\ClearglassAerospace-Master.ps1 -Mode DataCollection -CompanyFilter space_launch
```

### Generate Investment Recommendations
```powershell
.\ClearglassAerospace-Master.ps1 -Mode Prediction -EnablePredictiveML
```

### Continuous Market Monitoring
```powershell
.\ClearglassAerospace-Master.ps1 -Mode Monitor -EnableRealtime
```

═══════════════════════════════════════════════════════════════════

## 🔧 CUSTOMIZATION

Edit **config/clearglassinc.json** to:
- Add API keys for enhanced data collection
- Adjust analysis thresholds
- Configure ML models
- Customize report branding
- Set email notifications

═══════════════════════════════════════════════════════════════════

## 📞 NEED HELP?

**Full Documentation:** See README.md
**System Architecture:** docs/Clearglassinc_System_Architecture.docx
**Support:** support@clearglassinc.com
**Sales:** sales@clearglassinc.com

═══════════════════════════════════════════════════════════════════

## 📝 NEXT STEPS

1. ✅ Run your first analysis (above)
2. 📖 Review the generated reports
3. ⚙️ Customize configuration
4. 🔄 Schedule automated runs
5. 📊 Explore predictive forecasts

═══════════════════════════════════════════════════════════════════

## 💼 COMMERCIAL LICENSING

This is a commercial product available for enterprise licensing.

**Professional Edition:** Single user, annual subscription
**Enterprise Edition:** Unlimited users, perpetual license
**Source Code License:** Full source access with customization rights

Contact: sales@clearglassinc.com
Phone: 1-800-CLEARGLASS

═══════════════════════════════════════════════════════════════════

**Clearglassinc - Illuminating Aerospace Market Intelligence**

© 2025-2030 Clearglassinc. All Rights Reserved.
This software is proprietary and confidential.
