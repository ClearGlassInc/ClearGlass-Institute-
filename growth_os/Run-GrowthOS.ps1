param(
    [Parameter(Mandatory = $true)]
    [string]$Posts,

    [string]$Comments,

    [string]$Identity = (Join-Path $PSScriptRoot "config.example.json"),

    [string]$Topics = "AI,cybersecurity,policy,finance,Ontario",

    [string]$OutDir = (Join-Path $PSScriptRoot "output")
)

$ErrorActionPreference = "Stop"

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    $pythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $pythonCmd) {
    throw "Python is required but was not found in PATH."
}

$args = @(
    (Join-Path $PSScriptRoot "growth_os.py"),
    "--posts", $Posts,
    "--identity", $Identity,
    "--topics", $Topics,
    "--outdir", $OutDir
)

if ($Comments) {
    $args += @("--comments", $Comments)
}

& $pythonCmd.Source @args
