# Validate uploads and basic flows for Corpus Forge
# Usage: Open a PowerShell terminal in project root and run:
#   .\tools\validate_uploads.ps1

$base = 'http://127.0.0.1:5000'
$samples = Get-ChildItem -Path .\tools\upload_samples\* -File
if (-not $samples) { Write-Error "No sample files found in tools\upload_samples"; exit 1 }

$results = @()
foreach ($f in $samples) {
    Write-Host "Uploading $($f.Name)..."
    # Upload file
    $uploadOut = curl.exe -s -F "document=@$($f.FullName)" "$base/upload" -L -o upload_resp.html
    Start-Sleep -Milliseconds 300
    # Get last inserted document id
    $id = & .\.venv\Scripts\python.exe -c "import sqlite3;db=sqlite3.connect('data/corpus_forge.db');r=db.execute('SELECT id FROM documents ORDER BY id DESC LIMIT 1').fetchone(); print(r[0] if r else '')"
    if (-not $id) {
        Write-Warning "Failed to get document id after uploading $($f.Name)"
        $results += @{file = $f.Name; uploaded = $false; id = $null }
        continue
    }
    Write-Host "Uploaded as id $id"
    # Run a quick chat to verify retrieval (may return fallback)
    $chatRespFile = "chat_$id.html"
    curl.exe -s -d "active_documents=$id&question=What+is+this+document+about%3F&strategy=fixed" "$base/chat" -o $chatRespFile
    $chatSnippet = Select-String -Path $chatRespFile -Pattern "Grounded answer|No lexical overlap|Fallback match|confidence-" -AllMatches | ForEach-Object { $_.Line } | Out-String
    # Try generate flashcards for the doc
    $genResp = curl.exe -s -d "active_documents=$id&task=flashcards&query=main+ideas&strategy=fixed" "$base/generate" -o gen_resp.html -w "HTTP:%{http_code}"
    Start-Sleep -Milliseconds 300
    # Check artifacts page for a recent artifact title
    $artifactsHtml = curl.exe -s "$base/artifacts"
    $hasArtifact = ($artifactsHtml -match $f.Name) -or ($artifactsHtml -match 'Flashcards')
    $results += @{file = $f.Name; uploaded = $true; id = $id; chat = $chatSnippet; generated = $hasArtifact }
}

# Show summary
Write-Host "\nUpload validation summary:\n"
foreach ($r in $results) {
    Write-Host "File: $($r.file) - uploaded: $($r.uploaded) - id: $($r.id) - artifact_saved: $($r.generated)"
}

# Show /api/stats
$stats = curl.exe -s "$base/api/stats" | ConvertFrom-Json
Write-Host "\nAPI stats:"
$stats | ConvertTo-Json -Depth 3 | Write-Host

Write-Host "\nDetailed chat snippets saved to chat_<id>.html files in repo root."