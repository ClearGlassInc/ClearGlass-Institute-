<#
.SYNOPSIS
    Clearglassinc Aerospace Market Intelligence System - Master Orchestration
    Copyright © 2025-2030 Clearglassinc. All Rights Reserved.

.DESCRIPTION
    Enterprise-grade aerospace market intelligence automation platform
    Manages data collection, analysis, prediction, and reporting workflows
    
.NOTES
    Version: 5.0.0
    Author: Clearglassinc Development Team
    Architecture: Scalable microservices with predictive analytics
    
.PARAMETER Mode
    Operation mode: DataCollection, Analysis, Prediction, FullPipeline

.PARAMETER CompanyFilter
    Target companies (comma-separated) or "all" for full market scan

.PARAMETER OutputFormat  
    Report format: JSON, Excel, PDF, Dashboard

.EXAMPLE
    .\ClearglassAerospace-Master.ps1 -Mode FullPipeline -CompanyFilter "all" -OutputFormat Dashboard
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('DataCollection','Analysis','Prediction','FullPipeline','Monitor')]
    [string]$Mode = 'FullPipeline',
    
    [Parameter(Mandatory=$false)]
    [string]$CompanyFilter = 'aerospace_defense',
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('JSON','Excel','PDF','Dashboard','All')]
    [string]$OutputFormat = 'All',
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigPath = '../config/clearglassinc.json',
    
    [Parameter(Mandatory=$false)]
    [switch]$EnablePredictiveML,
    
    [Parameter(Mandatory=$false)]
    [switch]$EnableRealtime
)

# ═══════════════════════════════════════════════════════════════════════════
# CLEARGLASSINC BRANDING & INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

$Global:ClearglassVersion = "5.0.0"
$Global:Copyright = "© 2025-2030 Clearglassinc. All Rights Reserved."
$Global:SystemName = "Clearglassinc Aerospace Intelligence Platform"

function Write-ClearglassHeader {
    Clear-Host
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "   ______ _                      _                " -ForegroundColor White
    Write-Host "  / _____| | ___  __ _ _ __ __ _| | __ _ ___ ___  " -ForegroundColor White
    Write-Host " | |   | |/ _ \/ _\` | '__/ _\` | |/ _\` / __/ __| " -ForegroundColor White
    Write-Host " | |___| |  __/ (_| | | | (_| | | (_| \__ \__ \ " -ForegroundColor White
    Write-Host "  \____|_|\___|\__,_|_|  \__, |_|\__,_|___/___/ " -ForegroundColor White
    Write-Host "                         |___/                   " -ForegroundColor White
    Write-Host ""
    Write-Host "         AEROSPACE MARKET INTELLIGENCE SYSTEM" -ForegroundColor Cyan
    Write-Host "                  Version $Global:ClearglassVersion" -ForegroundColor Gray
    Write-Host "             $Global:Copyright" -ForegroundColor Gray
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION & ENVIRONMENT SETUP
# ═══════════════════════════════════════════════════════════════════════════

function Initialize-ClearglassEnvironment {
    param([string]$ConfigFile)
    
    Write-Host "[INIT] Loading Clearglassinc configuration..." -ForegroundColor Yellow
    
    # Load configuration
    if (Test-Path $ConfigFile) {
        $Global:Config = Get-Content $ConfigFile | ConvertFrom-Json
    } else {
        Write-Host "[ERROR] Configuration file not found: $ConfigFile" -ForegroundColor Red
        Write-Host "[INFO] Generating default configuration..." -ForegroundColor Yellow
        New-DefaultConfiguration -Path $ConfigFile
        $Global:Config = Get-Content $ConfigFile | ConvertFrom-Json
    }
    
    # Validate Python environment
    Write-Host "[INIT] Validating Python analytics engine..." -ForegroundColor Yellow
    $pythonCheck = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Python not found. Install Python 3.10+" -ForegroundColor Red
        exit 1
    }
    
    # Check required Python packages
    $requiredPackages = @(
        'pandas', 'numpy', 'scikit-learn', 'tensorflow', 
        'beautifulsoup4', 'requests', 'sqlalchemy', 
        'openpyxl', 'matplotlib', 'plotly'
    )
    
    Write-Host "[INIT] Checking Python dependencies..." -ForegroundColor Yellow
    foreach ($pkg in $requiredPackages) {
        $check = python -c "import $($pkg.Replace('-','_'))" 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  [INSTALL] $pkg" -ForegroundColor Cyan
            pip install $pkg --quiet
        } else {
            Write-Host "  [OK] $pkg" -ForegroundColor Green
        }
    }
    
    # Initialize database
    Write-Host "[INIT] Initializing Clearglassinc database..." -ForegroundColor Yellow
    & python ../python/database_init.py
    
    # Create output directories
    $outputDirs = @(
        'output/reports',
        'output/data',
        'output/predictions',
        'output/dashboards',
        'logs'
    )
    
    foreach ($dir in $outputDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    Write-Host "[SUCCESS] Clearglassinc environment initialized" -ForegroundColor Green
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# DATA COLLECTION MODULE
# ═══════════════════════════════════════════════════════════════════════════

function Invoke-DataCollection {
    param(
        [string]$Filter,
        [switch]$Realtime
    )
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║         DATA COLLECTION - Aerospace Market Intelligence       ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[START] Data collection initiated: $timestamp" -ForegroundColor Yellow
    Write-Host "[FILTER] Target sector: $Filter" -ForegroundColor Gray
    
    # Execute Python data collector
    $collectionScript = "../python/data_collector.py"
    Write-Host "[EXECUTE] Running data collector..." -ForegroundColor Yellow
    
    $args = @(
        $collectionScript,
        "--sector", $Filter,
        "--output", "output/data/raw_data_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    )
    
    if ($Realtime) {
        $args += "--realtime"
    }
    
    & python $args
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Data collection completed" -ForegroundColor Green
        Write-Host ""
        return $true
    } else {
        Write-Host "[ERROR] Data collection failed" -ForegroundColor Red
        Write-Host ""
        return $false
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# ANALYSIS MODULE
# ═══════════════════════════════════════════════════════════════════════════

function Invoke-MarketAnalysis {
    param([string]$DataPath)
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          MARKET ANALYSIS - Competitive Intelligence           ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    Write-Host "[ANALYZE] Processing market data..." -ForegroundColor Yellow
    
    $analysisScript = "../python/market_analyzer.py"
    $outputFile = "output/reports/analysis_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    & python $analysisScript --input $DataPath --output $outputFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Analysis completed" -ForegroundColor Green
        Write-Host "[OUTPUT] Results saved: $outputFile" -ForegroundColor Gray
        Write-Host ""
        return $outputFile
    } else {
        Write-Host "[ERROR] Analysis failed" -ForegroundColor Red
        Write-Host ""
        return $null
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# PREDICTIVE MODELING MODULE
# ═══════════════════════════════════════════════════════════════════════════

function Invoke-PredictiveModeling {
    param(
        [string]$AnalysisPath,
        [switch]$EnableML
    )
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║      PREDICTIVE MODELING - Future Market Forecasting          ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    if (-not $EnableML) {
        Write-Host "[SKIP] Predictive ML disabled. Use -EnablePredictiveML to activate" -ForegroundColor Yellow
        Write-Host ""
        return $null
    }
    
    Write-Host "[PREDICT] Generating market forecasts..." -ForegroundColor Yellow
    
    $predictionScript = "../python/predictive_engine.py"
    $outputFile = "output/predictions/forecast_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
    
    & python $predictionScript --analysis $AnalysisPath --output $outputFile --horizon 60
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[SUCCESS] Predictions generated" -ForegroundColor Green
        Write-Host "[OUTPUT] Forecast saved: $outputFile" -ForegroundColor Gray
        Write-Host ""
        return $outputFile
    } else {
        Write-Host "[ERROR] Prediction failed" -ForegroundColor Red
        Write-Host ""
        return $null
    }
}

# ═══════════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════

function New-ClearglassReport {
    param(
        [string]$DataPath,
        [string]$AnalysisPath,
        [string]$PredictionPath,
        [string]$Format
    )
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║            REPORT GENERATION - Clearglassinc Suite            ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    
    switch ($Format) {
        'Excel' {
            Write-Host "[GENERATE] Creating Excel report..." -ForegroundColor Yellow
            $output = "output/reports/Clearglassinc_Report_$timestamp.xlsx"
            & python ../python/report_generator.py --format excel --output $output `
                --data $DataPath --analysis $AnalysisPath --predictions $PredictionPath
        }
        'PDF' {
            Write-Host "[GENERATE] Creating PDF report..." -ForegroundColor Yellow
            $output = "output/reports/Clearglassinc_Report_$timestamp.pdf"
            & python ../python/report_generator.py --format pdf --output $output `
                --data $DataPath --analysis $AnalysisPath --predictions $PredictionPath
        }
        'Dashboard' {
            Write-Host "[GENERATE] Launching interactive dashboard..." -ForegroundColor Yellow
            & python ../python/dashboard_server.py --data $DataPath --analysis $AnalysisPath
        }
        'All' {
            Write-Host "[GENERATE] Creating comprehensive report suite..." -ForegroundColor Yellow
            New-ClearglassReport -DataPath $DataPath -AnalysisPath $AnalysisPath `
                -PredictionPath $PredictionPath -Format 'Excel'
            New-ClearglassReport -DataPath $DataPath -AnalysisPath $AnalysisPath `
                -PredictionPath $PredictionPath -Format 'PDF'
        }
    }
    
    Write-Host "[SUCCESS] Reports generated" -ForegroundColor Green
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════

function Start-ClearglassPipeline {
    Write-ClearglassHeader
    Initialize-ClearglassEnvironment -ConfigFile $ConfigPath
    
    $startTime = Get-Date
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║               STARTING CLEARGLASSINC PIPELINE                  ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    
    $dataPath = $null
    $analysisPath = $null
    $predictionPath = $null
    
    # Execute based on mode
    switch ($Mode) {
        'DataCollection' {
            $success = Invoke-DataCollection -Filter $CompanyFilter -Realtime:$EnableRealtime
            if (-not $success) { exit 1 }
        }
        
        'Analysis' {
            $latestData = Get-ChildItem "output/data" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $analysisPath = Invoke-MarketAnalysis -DataPath $latestData.FullName
        }
        
        'Prediction' {
            $latestAnalysis = Get-ChildItem "output/reports" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $predictionPath = Invoke-PredictiveModeling -AnalysisPath $latestAnalysis.FullName -EnableML:$EnablePredictiveML
        }
        
        'FullPipeline' {
            # Step 1: Data Collection
            $success = Invoke-DataCollection -Filter $CompanyFilter -Realtime:$EnableRealtime
            if (-not $success) { exit 1 }
            
            $dataPath = Get-ChildItem "output/data" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Select-Object -ExpandProperty FullName
            
            # Step 2: Analysis
            $analysisPath = Invoke-MarketAnalysis -DataPath $dataPath
            if (-not $analysisPath) { exit 1 }
            
            # Step 3: Prediction (if enabled)
            if ($EnablePredictiveML) {
                $predictionPath = Invoke-PredictiveModeling -AnalysisPath $analysisPath -EnableML
            }
            
            # Step 4: Report Generation
            New-ClearglassReport -DataPath $dataPath -AnalysisPath $analysisPath `
                -PredictionPath $predictionPath -Format $OutputFormat
        }
        
        'Monitor' {
            Write-Host "[MONITOR] Starting continuous monitoring mode..." -ForegroundColor Yellow
            Write-Host "[INFO] Press Ctrl+C to stop" -ForegroundColor Gray
            Write-Host ""
            
            while ($true) {
                Invoke-DataCollection -Filter $CompanyFilter -Realtime
                Start-Sleep -Seconds 3600  # Run every hour
            }
        }
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host "╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║           CLEARGLASSINC PIPELINE COMPLETED                     ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "[COMPLETE] Total execution time: $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Cyan
    Write-Host "[TIMESTAMP] $endTime" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Clearglassinc © 2025-2030. All Rights Reserved." -ForegroundColor DarkGray
    Write-Host ""
}

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

function New-DefaultConfiguration {
    param([string]$Path)
    
    $defaultConfig = @{
        "system" = @{
            "name" = "Clearglassinc Aerospace Intelligence"
            "version" = $Global:ClearglassVersion
            "copyright" = $Global:Copyright
        }
        "data_sources" = @{
            "public_apis" = @(
                "https://api.spacexdata.com/v4/",
                "https://api.nasa.gov/",
                "https://api.sec.gov/"
            )
            "industry_databases" = @(
                "aerospace_companies.db",
                "contracts.db",
                "market_data.db"
            )
        }
        "analysis" = @{
            "metrics" = @(
                "market_share",
                "revenue_growth",
                "contract_volume",
                "innovation_index",
                "competitive_positioning"
            )
            "refresh_interval" = 3600
        }
        "ml_models" = @{
            "enabled" = $true
            "algorithms" = @("LSTM", "RandomForest", "GradientBoosting")
            "forecast_horizon_days" = 90
            "confidence_threshold" = 0.85
        }
        "output" = @{
            "formats" = @("Excel", "PDF", "JSON", "Dashboard")
            "retention_days" = 365
        }
    }
    
    $defaultConfig | ConvertTo-Json -Depth 10 | Out-File $Path -Encoding UTF8
    Write-Host "[CREATED] Default configuration: $Path" -ForegroundColor Green
}

# ═══════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

# Execute main pipeline
Start-ClearglassPipeline

# End of Clearglassinc Aerospace Intelligence System
# © 2025-2030 Clearglassinc. All Rights Reserved.
