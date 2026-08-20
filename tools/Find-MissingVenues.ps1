param([int]$Days = 35, [int]$MinAttending = 50)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$BaseDir = "C:\gl030-import"
$Handler = "https://import.gaesteliste030.de/Handler/EventImportHandler.ashx"
$Resolve = "import.gaesteliste030.de:443:127.0.0.1"
$UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
$Key = [Environment]::GetEnvironmentVariable("GL030_EVENTIMPORT_KEY","Machine")
if (-not $Key) { $Key = $env:GL030_EVENTIMPORT_KEY }
if (-not $Key) { throw "GL030_EVENTIMPORT_KEY nicht gesetzt." }

function Nrm([string]$s) {
    if (-not $s) { return "" }
    $s = $s.ToLower()
    $s = $s.Replace([string][char]0xE4,"ae").Replace([string][char]0xF6,"oe")
    $s = $s.Replace([string][char]0xFC,"ue").Replace([string][char]0xDF,"ss")
    return ($s -replace "[^a-z0-9]","")
}

function Look([string]$q) {
    $u = $Handler + "?action=lookup&type=location&q=" + [uri]::EscapeDataString($q)
    $raw = & curl.exe -sk --resolve $Resolve $u -H ("X-Import-Key: " + $Key) 2>$null
    $t = ($raw | Out-String).Trim()
    if (-not $t) { return $null }
    return ($t | ConvertFrom-Json)
}

$Q = 'query($filters: FilterInputDtoInput, $pageSize: Int, $page: Int) { eventListings(filters: $filters, pageSize: $pageSize, page: $page) { data { event { id venue { id name } attending } } totalResults } }'
$from = (Get-Date).ToString("yyyy-MM-dd")
$to = (Get-Date).AddDays($Days).ToString("yyyy-MM-dd")
$ev = @{}
$total = $null
for ($p = 1; $p -le 15; $p++) {
    $vars = @{ filters = @{ areas = @{ eq = 34 }; listingDate = @{ gte = $from; lte = $to } }; pageSize = 100; page = $p }
    $body = @{ query = $Q; variables = $vars } | ConvertTo-Json -Depth 10 -Compress
    $r = Invoke-RestMethod -Method Post -Uri "https://ra.co/graphql" -ContentType "application/json" -Headers @{ "User-Agent" = $UA } -Body $body -TimeoutSec 60
    $chunk = @($r.data.eventListings.data)
    if ($null -eq $total) { $total = $r.data.eventListings.totalResults }
    foreach ($row in $chunk) { if ($row.event) { $ev[[string]$row.event.id] = $row.event } }
    if ($chunk.Count -lt 100 -or ($p * 100) -ge $total) { break }
    Start-Sleep -Milliseconds 500
}
Write-Host ("RA: " + $ev.Count + " Events, Fenster " + $from + " bis " + $to) -ForegroundColor Cyan

$V = @{}
foreach ($e in $ev.Values) {
    if (-not $e.venue) { continue }
    $n = [string]$e.venue.name
    if (-not $n) { continue }
    if (-not $V.ContainsKey($n)) { $V[$n] = [pscustomobject]@{ name = $n; n = 0; att = 0 } }
    $V[$n].n++
    $V[$n].att += [int]$e.attending
}

$Clubs = @{}
$cf = Join-Path $BaseDir "clubs.txt"
if (Test-Path $cf) {
    foreach ($line in (Get-Content $cf -Encoding UTF8)) {
        $t = $line.Trim()
        if (-not $t) { continue }
        if ($t.StartsWith("#")) { continue }
        $al = $null
        if ($t.Contains("=")) { $q2 = $t.Split("=",2); $t = $q2[0].Trim(); $al = $q2[1].Trim() }
        $Clubs[(Nrm $t)] = $al
    }
}

$ok = @(); $addWl = @(); $aliasC = @(); $missing = @()
$list = @($V.Values | Where-Object { $_.att -ge $MinAttending } | Sort-Object att -Descending)
$i = 0
foreach ($v in $list) {
    $i++
    Write-Progress -Activity "Lookup" -Status $v.name -PercentComplete (100 * $i / $list.Count)
    $nk = Nrm $v.name
    $onWl = $Clubs.ContainsKey($nk)
    $tries = @()
    if ($onWl -and $Clubs[$nk]) { $tries += $Clubs[$nk] }
    $tries += $v.name
    if ($v.name -match "(?i)\sberlin$") { $tries += ($v.name -replace "(?i)\sberlin$","") }
    $hit = $null
    $cands = @()
    foreach ($t in $tries) {
        Start-Sleep -Milliseconds 120
        $r = $null
        try { $r = Look $t } catch { }
        if (-not $r) { continue }
        $exact = @($r.results | Where-Object { $_.match -eq "exact" -and $_.isApproved -eq $true })
        if ($exact.Count -eq 1) { $hit = $exact[0].name; break }
        foreach ($c in @($r.results | Where-Object { $_.isApproved -eq $true } | Select-Object -First 3)) { $cands += $c.name }
    }
    $row = "{0} | Events {1} | Interesse {2}" -f $v.name, $v.n, $v.att
    if ($hit -and $onWl) { $ok += $row }
    elseif ($hit) { $addWl += ($row + " -> Location: '" + $hit + "'") }
    elseif ($cands.Count -gt 0) { $aliasC += ($row + " -> Kandidaten: " + ((@($cands | Select-Object -Unique)) -join " / ")) }
    else { $missing += $row }
}

$md = @()
$md += "# GL030 Venue-Abdeckung " + (Get-Date -Format "yyyy-MM-dd HH:mm")
$md += ""
$md += "RA Berlin, " + $Days + " Tage (" + $from + " bis " + $to + ") | Events: " + $ev.Count + " | geprueft ab " + $MinAttending + " Interesse: " + $list.Count + " Venues"
$md += ""
$md += "## A) Location vorhanden, NICHT auf Whitelist -> nur clubs.txt-Zeile (" + $addWl.Count + ")"
foreach ($x in $addWl) { $md += "- " + $x }
$md += ""
$md += "## B) Alias-Kandidat: kein exakter Treffer, aehnliche Location da (" + $aliasC.Count + ")"
foreach ($x in $aliasC) { $md += "- " + $x }
$md += ""
$md += "## C) Location fehlt wirklich -> im Admin anlegen (" + $missing.Count + ")"
foreach ($x in $missing) { $md += "- " + $x }
$md += ""
$md += "## D) Gelistet und aufloesbar (" + $ok.Count + ")"
foreach ($x in $ok) { $md += "- " + $x }

$out = ($md -join "`r`n")
$dir = Join-Path $BaseDir "reports"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
$path = Join-Path $dir ("venue-abdeckung-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".md")
[IO.File]::WriteAllText($path, $out, (New-Object System.Text.UTF8Encoding($false)))
Write-Output $out
Write-Host ""
Write-Host ("Gespeichert: " + $path) -ForegroundColor Green
