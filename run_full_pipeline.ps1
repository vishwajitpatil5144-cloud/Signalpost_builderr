param(
    [Parameter(Mandatory = $true)][string]$Organisations,
    [Parameter(Mandatory = $true)][string]$Bulk,
    [Parameter(Mandatory = $true)][int]$ExpectedCount,
    [Parameter(Mandatory = $true)][string]$RunId
)

$ErrorActionPreference = "Stop"
$outDir = "out"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

Write-Host "== [1/5] Registry + registry-website batch =="
uv run python scripts/run_competition_batch.py `
    --organisations $Organisations `
    --bulk $Bulk `
    --profiles-output "$outDir/profiles.jsonl" `
    --output "$outDir/envelopes.jsonl" `
    --report "$outDir/run-report.json" `
    --run-id $RunId `
    --expected-count $ExpectedCount

Write-Host "== [2/5] Free website discovery for the rest =="
uv run python scripts/run_free_domain_discovery.py `
    --input "$outDir/profiles.jsonl" `
    --output "$outDir/profiles-with-discovery.jsonl" `
    --report "$outDir/discovery-report.json" `
    --promote-verified

Write-Host "== [3/5] Deterministic synthesis =="
uv run python scripts/generate_synthesis.py `
    --input "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/synthesis.jsonl"

Write-Host "== [4/5] Browsable showcase site =="
uv run python scripts/build_prototype.py `
    --input "$outDir/envelopes.jsonl" `
    --output "$outDir/showcase.html"

# This is the contract-facing file; envelopes.jsonl remains an internal shape.
Write-Host "== [5/5] Export contract-compliant terminal envelopes =="
uv run python scripts/export_terminal_envelopes.py `
    --input "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/terminal-envelopes.jsonl" `
    --run-id $RunId

Write-Host "Done. Submit $outDir/terminal-envelopes.jsonl"