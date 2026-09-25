[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Organisations,

    [Parameter(Mandatory = $true)]
    [string]$Bulk,

    [Parameter(Mandatory = $true)]
    [int]$ExpectedCount,

    [Parameter(Mandatory = $true)]
    [string]$RunId,

    [Parameter(Mandatory = $false)]
    [string]$OutDir = "out"
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

Write-Host "== [1/6] Registry + registry-website batch =="
uv run python scripts/run_competition_batch.py `
    --organisations $Organisations `
    --bulk $Bulk `
    --profiles-output "$outDir/profiles.jsonl" `
    --output "$outDir/envelopes.jsonl" `
    --report "$outDir/run-report.json" `
    --run-id $RunId `
    --expected-count $ExpectedCount

Write-Host "== [2/6] Free website discovery for the rest =="
uv run python scripts/run_free_domain_discovery.py `
    --input "$outDir/profiles.jsonl" `
    --output "$outDir/profiles-with-discovery.jsonl" `
    --report "$outDir/discovery-report.json" `
    --promote-verified

Write-Host "== [3/6] External footprint & signal connectors =="
uv run python scripts/extract_company_site_activity.py `
    --profiles "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/activity.jsonl" `
    --report "$outDir/activity-report.json"
uv run python scripts/extract_company_site_news.py `
    --profiles "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/news.jsonl" `
    --report "$outDir/news-report.json"
uv run python scripts/extract_company_hiring_signal.py `
    --profiles "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/hiring.jsonl" `
    --report "$outDir/hiring-report.json"
uv run python scripts/run_wikidata_connector.py `
    --profiles "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/wikidata.jsonl" `
    --report "$outDir/wikidata-report.json"
uv run python scripts/run_nominatim_connector.py `
    --profiles "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/nominatim.jsonl" `
    --report "$outDir/nominatim-report.json"
uv run python scripts/run_nav_arbeidsplassen_connector.py `
    --profiles "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/nav.jsonl" `
    --report "$outDir/nav-report.json"

Write-Host "== [4/6] Deterministic synthesis =="
uv run python scripts/generate_synthesis.py `
    --input "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/synthesis.jsonl" `
    --activity "$outDir/activity.jsonl" `
    --news "$outDir/news.jsonl" `
    --hiring "$outDir/hiring.jsonl" `
    --wikidata "$outDir/wikidata.jsonl" `
    --nominatim "$outDir/nominatim.jsonl" `
    --nav "$outDir/nav.jsonl"

Write-Host "== [5/6] Browsable showcase site =="
try {
    uv run python scripts/build_prototype.py `
        --input "$outDir/profiles-with-discovery.jsonl" `
        --external-observations `
            "$outDir/activity.jsonl" `
            "$outDir/news.jsonl" `
            "$outDir/hiring.jsonl" `
            "$outDir/wikidata.jsonl" `
            "$outDir/nominatim.jsonl" `
            "$outDir/nav.jsonl" `
        --output "$outDir/showcase.html"
} catch {
    Write-Host "(showcase build skipped/failed -- check scripts/build_prototype.py --help)"
}

# This is the contract-facing file; envelopes.jsonl remains an internal shape.
Write-Host "== [6/6] Export contract-compliant terminal envelopes =="
uv run python scripts/export_terminal_envelopes.py `
    --input "$outDir/profiles-with-discovery.jsonl" `
    --output "$outDir/terminal-envelopes.jsonl" `
    --run-id $RunId `
    --activity "$outDir/activity.jsonl" `
    --news "$outDir/news.jsonl" `
    --hiring "$outDir/hiring.jsonl" `
    --wikidata "$outDir/wikidata.jsonl" `
    --nominatim "$outDir/nominatim.jsonl" `
    --nav "$outDir/nav.jsonl"

Write-Host ""
Write-Host "Done. Key outputs:"
Write-Host "  $outDir/terminal-envelopes.jsonl   (submission artifact)"
Write-Host "  $outDir/envelopes.jsonl            (internal envelope shape)"
Write-Host "  $outDir/profiles-with-discovery.jsonl"
Write-Host "  $outDir/synthesis.jsonl            (decision-useful summaries)"
Write-Host "  $outDir/showcase.html              (browsable UI)"
Write-Host "  $outDir/run-report.json, $outDir/discovery-report.json  (cost/request accounting)"
