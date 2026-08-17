# GL030 Event-Import: Resident Advisor -> EventImportHandler (lokal)
# Regeln R1-R10 (16.08.2026). Laeuft als geplante Aufgabe (SYSTEM).
# Aufruf: Import-RaEvents.ps1 -Days 35 [-DryRun]
param(
    [int]$Days = 35,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[System.Net.ServicePointManager]::ServerCertificateValidationCallback = { $true }

$BaseDir    = "C:\gl030-import"
$ReportDir  = Join-Path $BaseDir "reports"
$VenueMap   = Join-Path $BaseDir "venue-map.json"
$TokenFile  = Join-Path $BaseDir "github.token"
$HandlerUrl = "https://import.gaesteliste030.de/Handler/EventImportHandler.ashx"
$Resolve    = "import.gaesteliste030.de:443:127.0.0.1"
$UserAgent  = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
$RaAreaBerlin = 34
$MaxPages   = 15

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

# --- Key aus Maschinen-Umgebung (nie im Skript) ---
$Key = [Environment]::GetEnvironmentVariable("GL030_EVENTIMPORT_KEY", "Machine")
if (-not $Key) { $Key = $env:GL030_EVENTIMPORT_KEY }
if (-not $Key) { throw "GL030_EVENTIMPORT_KEY nicht gesetzt." }

# --- Helfer ---
function Normalize([string]$s) {
    if (-not $s) { return "" }
    $s = $s.ToLower()
    $s = $s.Replace([string][char]0xE4, "ae").Replace([string][char]0xF6, "oe")
    $s = $s.Replace([string][char]0xFC, "ue").Replace([string][char]0xDF, "ss")
    return ($s -replace "[^a-z0-9]", "")
}

function Invoke-Handler([string]$Action, [string]$Query, [string]$BodyFile) {
    $url = "$HandlerUrl`?action=$Action"
    if ($Query) { $url += "&$Query" }
    if ($BodyFile) {
        $raw = & curl.exe -sk --resolve $Resolve $url -H "X-Import-Key: $Key" -H "Content-Type: application/json" --data-binary "@$BodyFile" 2>$null
    } else {
        $raw = & curl.exe -sk --resolve $Resolve $url -H "X-Import-Key: $Key" 2>$null
    }
    $text = ($raw | Out-String).Trim()
    if (-not $text) { throw "Leere Antwort vom Handler ($Action)." }
    return ($text | ConvertFrom-Json)
}

function Invoke-Ra([string]$Query, $Variables) {
    $body = @{ query = $Query; variables = $Variables } | ConvertTo-Json -Depth 10 -Compress
    return Invoke-RestMethod -Method Post -Uri "https://ra.co/graphql" -ContentType "application/json" `
        -Headers @{ "User-Agent" = $UserAgent } -Body $body -TimeoutSec 60
}

# --- R4: Genre -> Kategorie ---
$HipHopGenres = @("hip hop", "hip-hop", "r&b", "rnb", "trap", "rap", "afrobeats", "dancehall", "reggaeton")
function Map-Category($Genres, [string]$Title) {
    $names = @()
    foreach ($g in $Genres) { $names += ([string]$g.name).ToLower() }
    $primary = "Electro"
    $isHipHop = $false
    foreach ($n in $names) { foreach ($h in $HipHopGenres) { if ($n -like "*$h*") { $isHipHop = $true } } }
    if ($isHipHop) { $primary = "Hip Hop" }
    elseif ($names.Count -eq 0) { $primary = "Party" }
    $cats = @($primary)
    if ($Title -match "(?i)open[\s-]?air") { $cats += "Open Air" }
    return $cats
}

# --- R6: eigene Kurztexte (Fakten, keine RA-Prosa). HTML-Entities statt Umlauten. ---
$Months = @{ 1="Januar";2="Februar";3="M&auml;rz";4="April";5="Mai";6="Juni";7="Juli";8="August";9="September";10="Oktober";11="November";12="Dezember" }
$WdDe = @{ Monday="Montag";Tuesday="Dienstag";Wednesday="Mittwoch";Thursday="Donnerstag";Friday="Freitag";Saturday="Samstag";Sunday="Sonntag" }
$MonthsEn = @{ 1="January";2="February";3="March";4="April";5="May";6="June";7="July";8="August";9="September";10="October";11="November";12="December" }
$MonthsEs = @{ 1="enero";2="febrero";3="marzo";4="abril";5="mayo";6="junio";7="julio";8="agosto";9="septiembre";10="octubre";11="noviembre";12="diciembre" }
$WdEs = @{ Monday="lunes";Tuesday="martes";Wednesday="mi&eacute;rcoles";Thursday="jueves";Friday="viernes";Saturday="s&aacute;bado";Sunday="domingo" }

function Build-Content($Title, $VenueName, [datetime]$Begin, [datetime]$End, $Genres, $ArtistNames) {
    $gtxt = ""
    if ($Genres -and $Genres.Count -gt 0) {
        $gnames = @(); foreach ($g in $Genres) { $gnames += $g.name }
        $gtxt = ($gnames -join ", ")
    }
    $atxt = ""
    if ($ArtistNames -and $ArtistNames.Count -gt 0) {
        $top = $ArtistNames | Select-Object -First 3
        $atxt = ($top -join ", ")
        if ($ArtistNames.Count -gt 3) { $atxt += " u. a." }
    }
    $wd = [string]$Begin.DayOfWeek
    $de = "<p>$Title im $VenueName" + ": am " + $WdDe[$wd] + ", " + $Begin.Day + ". " + $Months[[int]$Begin.Month] + " ab " + $Begin.ToString("HH:mm") + " Uhr" + $(if ($End) { " bis " + $End.ToString("HH:mm") + " Uhr" } else { "" }) + "."
    if ($gtxt) { $de += " Musikalisch stehen $gtxt auf dem Programm." }
    if ($atxt) { $de += " Mit dabei: $atxt." }
    $de += " Alle Infos und die G&auml;steliste findest du hier auf G&auml;steliste030.</p>"
    $en = "<p>$Title at $VenueName" + ": " + $wd + ", " + $MonthsEn[[int]$Begin.Month] + " " + $Begin.Day + ", from " + $Begin.ToString("HH:mm") + $(if ($End) { " until " + $End.ToString("HH:mm") } else { "" }) + "."
    if ($gtxt) { $en += " Expect $gtxt on the floors." }
    if ($atxt) { $en += " Line-up includes $atxt." }
    $en += " Guest list and details right here on Gaesteliste030.</p>"
    $es = "<p>$Title en $VenueName" + ": el " + $WdEs[$wd] + " " + $Begin.Day + " de " + $MonthsEs[[int]$Begin.Month] + ", desde las " + $Begin.ToString("HH:mm") + $(if ($End) { " hasta las " + $End.ToString("HH:mm") } else { "" }) + "."
    if ($gtxt) { $es += " Sonar&aacute;n $gtxt." }
    if ($atxt) { $es += " Con $atxt." }
    $es += " Lista de invitados y detalles aqu&iacute; en Gaesteliste030.</p>"
    return @{ de = $de; en = $en; es = $es }
}

# --- Venue-Map laden ---
$Map = @{}
if (Test-Path $VenueMap) {
    $obj = Get-Content $VenueMap -Raw | ConvertFrom-Json
    foreach ($p in $obj.PSObject.Properties) { $Map[$p.Name] = $p.Value }
}

# --- Club-Liste (Whitelist mit optionalem Alias) ---
$ClubFile = Join-Path $BaseDir "clubs.txt"
# Bei jedem Lauf frisch aus dem Repo ziehen (Pflege ohne Server-Handgriff); Fallback: lokale Datei
if (Test-Path $TokenFile) {
    try {
        $ghTok = (Get-Content $TokenFile -Raw).Trim()
        $ghHdr = @{ Authorization = "token $ghTok"; "User-Agent" = "gl030-import"; Accept = "application/vnd.github.raw" }
        Invoke-RestMethod -Uri "https://api.github.com/repos/gl030/gl030-sitemap/contents/tools/clubs.txt" -Headers $ghHdr -OutFile $ClubFile -TimeoutSec 30
    } catch { Write-Output ("clubs.txt-Refresh fehlgeschlagen, nutze lokale Datei: " + $_.Exception.Message) }
}
$Clubs = @{}
if (Test-Path $ClubFile) {
    foreach ($line in (Get-Content $ClubFile -Encoding UTF8)) {
        $t = $line.Trim()
        if (-not $t -or $t.StartsWith("#")) { continue }
        $alias = $null
        if ($t.Contains("=")) {
            $pieces = $t.Split("=", 2)
            $t = $pieces[0].Trim()
            $alias = $pieces[1].Trim()
        }
        $Clubs[(Normalize $t)] = @{ raw = $t; alias = $alias }
    }
}
if ($Clubs.Count -eq 0) { throw "clubs.txt fehlt oder ist leer - Lauf abgebrochen (Whitelist ist Pflicht)." }

$RunCache = @{}
function Resolve-Venue([string]$RaVenueId, [string]$RaVenueName, [string]$Alias) {
    if ($Map.ContainsKey($RaVenueId)) { return $Map[$RaVenueId] }
    if ($RunCache.ContainsKey($RaVenueId)) { return $RunCache[$RaVenueId] }
    $tries = @()
    if ($Alias) { $tries += $Alias }
    $tries += $RaVenueName
    if ($RaVenueName -match "(?i)\sberlin$") { $tries += ($RaVenueName -replace "(?i)\sberlin$", "") }
    foreach ($t in $tries) {
        Start-Sleep -Milliseconds 150
        try {
            $r = Invoke-Handler "lookup" ("type=location&q=" + [uri]::EscapeDataString($t)) $null
        } catch { continue }
        $exact = @($r.results | Where-Object { $_.match -eq "exact" })
        if ($exact.Count -eq 1) {
            $entry = [pscustomobject]@{ locationId = $exact[0].id; glName = $exact[0].name; status = "ok"; raName = $RaVenueName }
            $Map[$RaVenueId] = $entry
            return $entry
        }
    }
    $entry = [pscustomobject]@{ locationId = $null; glName = $null; status = "missing"; raName = $RaVenueName }
    $RunCache[$RaVenueId] = $entry
    return $entry
}

# --- RA: Listing holen ---
$From = (Get-Date).ToString("yyyy-MM-dd")
$To   = (Get-Date).AddDays($Days).ToString("yyyy-MM-dd")
$ListQuery = "query(`$filters: FilterInputDtoInput, `$pageSize: Int, `$page: Int) { eventListings(filters: `$filters, pageSize: `$pageSize, page: `$page) { data { event { id title date startTime endTime contentUrl venue { id name } attending artists { name } genres { name } images { filename } } } totalResults } }"

$Events = @{}
$total = $null
for ($page = 1; $page -le $MaxPages; $page++) {
    $vars = @{ filters = @{ areas = @{ eq = $RaAreaBerlin }; listingDate = @{ gte = $From; lte = $To } }; pageSize = 100; page = $page }
    $resp = Invoke-Ra $ListQuery $vars
    $chunk = @($resp.data.eventListings.data)
    if ($null -eq $total) { $total = $resp.data.eventListings.totalResults }
    foreach ($row in $chunk) {
        $e = $row.event
        if ($e -and -not $Events.ContainsKey([string]$e.id)) { $Events[[string]$e.id] = $e }
    }
    if ($chunk.Count -lt 100 -or ($page * 100) -ge $total) { break }
    Start-Sleep -Milliseconds 500
}

# --- Verarbeiten ---
$Created = @(); $Duplicates = @(); $Errors = @(); $NoVenue = 0
$MissingVenues = @{}

$SkippedNotListed = 0
foreach ($e in ($Events.Values | Sort-Object { $_.date })) {
    if (-not $e.venue -or -not $e.venue.id) { $NoVenue++; continue }
    $clubKey = Normalize ([string]$e.venue.name)
    if (-not $Clubs.ContainsKey($clubKey)) { $SkippedNotListed++; continue }
    $v = Resolve-Venue ([string]$e.venue.id) ([string]$e.venue.name) ([string]$Clubs[$clubKey].alias)
    if ($v.status -ne "ok") {
        $k = [string]$e.venue.name
        if (-not $MissingVenues.ContainsKey($k)) { $MissingVenues[$k] = [pscustomobject]@{ count = 0; attending = 0 } }
        $MissingVenues[$k].count++
        $MissingVenues[$k].attending += [int]$e.attending
        continue
    }

    if (([string]$e.title) -match "(?i)cancell?ed|abgesagt") { continue }
    $begin = [datetime]::ParseExact(([string]$e.startTime).Substring(0, 19), "yyyy-MM-ddTHH:mm:ss", [Globalization.CultureInfo]::InvariantCulture)
    if ($begin -lt (Get-Date).Date) { continue }
    $end = $null
    if ($e.endTime) { $end = [datetime]::ParseExact(([string]$e.endTime).Substring(0, 19), "yyyy-MM-ddTHH:mm:ss", [Globalization.CultureInfo]::InvariantCulture) }
    if (-not $end) { $end = $begin.AddHours(6) }

    $artistNames = @()
    if ($e.artists) { foreach ($a in $e.artists) { if ($a.name) { $artistNames += [string]$a.name } } }
    $artistNames = @($artistNames | Select-Object -First 30)

    $cats = @(Map-Category $e.genres ([string]$e.title))
    $content = Build-Content ([string]$e.title) ([string]$v.glName) $begin $end $e.genres $artistNames

    $music = ""
    if ($e.genres) { $gn = @(); foreach ($g in $e.genres) { $gn += $g.name }; $music = ($gn -join ", ") }

    $flyer = $null
    if ($e.images -and $e.images.Count -gt 0 -and $e.images[0].filename) { $flyer = [string]$e.images[0].filename }

    $payload = [ordered]@{
        externalId  = "ra:" + $e.id
        source      = "ra"
        sourceUrl   = "https://ra.co" + [string]$e.contentUrl
        name        = [string]$e.title
        locationId  = [string]$v.locationId
        begin       = $begin.ToString("yyyy-MM-ddTHH:mm:ss")
        end         = $end.ToString("yyyy-MM-ddTHH:mm:ss")
        music       = $music
        categoryNames = $cats
        artistNames = $artistNames
        longContent = $content
        ticketUrl   = "https://ra.co" + [string]$e.contentUrl
    }
    if ($flyer) { $payload["flyerUrl"] = $flyer; $payload["flyerReferer"] = "https://ra.co/" }

    $label = "{0} | {1} | {2}" -f $begin.ToString("dd.MM. HH:mm"), $v.glName, $e.title

    if ($DryRun) {
        try {
            Start-Sleep -Milliseconds 150
            $d = Invoke-Handler "duplicates" ("locationId=" + $v.locationId + "&date=" + $begin.ToString("yyyy-MM-dd") + "&externalId=" + [uri]::EscapeDataString("ra:" + $e.id)) $null
            $nrm = Normalize ([string]$e.title)
            $isDup = $false
            if ($d.alreadyImportedExternalId) { $isDup = $true }
            foreach ($x in @($d.results)) { if ((Normalize ([string]$x.name)) -eq $nrm) { $isDup = $true } }
            if ($isDup) { $Duplicates += $label } else { $Created += $label }
        } catch { $Errors += ($label + " :: " + $_.Exception.Message) }
        continue
    }

    $tmp = Join-Path $env:TEMP ("gl030-import-" + $e.id + ".json")
    [IO.File]::WriteAllText($tmp, ($payload | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
    try {
        Start-Sleep -Milliseconds 300
        $r = Invoke-Handler "create" $null $tmp
        if ($r.status -eq "error" -and ([string]$r.message) -like "*No category resolved*") {
            $payload["categoryNames"] = @("Electro")
            [IO.File]::WriteAllText($tmp, ($payload | ConvertTo-Json -Depth 6), (New-Object System.Text.UTF8Encoding($false)))
            Start-Sleep -Milliseconds 300
            $r = Invoke-Handler "create" $null $tmp
            if ($r.status -eq "created") { $label += " (Kategorie-Fallback: Electro - bitte pruefen)" }
        }
        switch ($r.status) {
            "created"           { $note = ""; if ($r.unmatchedArtists -and $r.unmatchedArtists.Count -gt 0) { $note = " (Artists unbekannt: " + $r.unmatchedArtists.Count + ")" }; $Created += ($label + $note) }
            "duplicate-import"  { $Duplicates += ($label + " [ExternalId]") }
            "duplicate-event"   { $Duplicates += ($label + " [Name+Tag]") }
            "location-unmatched" { $Errors += ($label + " :: Location nicht eindeutig") }
            default             { $Errors += ($label + " :: " + $r.status + " " + $r.message) }
        }
    } catch {
        $Errors += ($label + " :: " + $_.Exception.Message)
    } finally {
        Remove-Item $tmp -ErrorAction SilentlyContinue
    }
}

# --- Venue-Map speichern ---
$Map | ConvertTo-Json -Depth 5 | Set-Content -Path $VenueMap -Encoding UTF8

# --- Report ---
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$mode = ""
if ($DryRun) { $mode = " (PROBELAUF - nichts angelegt)" }
$md = @()
$md += "# GL030 Event-Import $stamp$mode"
$md += ""
$md += "Fenster: $From bis $To ($Days Tage) | RA-Events gesamt: $($Events.Count) | ohne Venue: $NoVenue | ausserhalb Club-Liste: $SkippedNotListed"
$md += ""
$md += "## Angelegt ($($Created.Count))"
foreach ($x in $Created) { $md += "- $x" }
$md += ""
$md += "## Dubletten ($($Duplicates.Count))"
foreach ($x in $Duplicates) { $md += "- $x" }
$md += ""
$md += "## Club fehlt ($($MissingVenues.Count) Venues)"
foreach ($k in ($MissingVenues.Keys | Sort-Object { $MissingVenues[$_].attending } -Descending)) {
    $md += "- $k | Events: $($MissingVenues[$k].count) | RA-Interesse: $($MissingVenues[$k].attending)"
}
$md += ""
$md += "## Fehler ($($Errors.Count))"
foreach ($x in $Errors) { $md += "- $x" }
$Report = ($md -join "`r`n")

$fileName = "import-" + (Get-Date -Format "yyyyMMdd-HHmmss") + $(if ($DryRun) { "-dryrun" } else { "" }) + ".md"
$localPath = Join-Path $ReportDir $fileName
[IO.File]::WriteAllText($localPath, $Report, (New-Object System.Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $ReportDir "latest.md"), $Report, (New-Object System.Text.UTF8Encoding($false)))
Write-Output $Report

# --- GitHub-Upload (Repo gl030/gl030-sitemap, Pfad reports/import/) ---
if (Test-Path $TokenFile) {
    try {
        $tok = (Get-Content $TokenFile -Raw).Trim()
        $hdr = @{ Authorization = "token $tok"; "User-Agent" = "gl030-import" }
        $b64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Report))
        $api = "https://api.github.com/repos/gl030/gl030-sitemap/contents/reports/import/"
        Invoke-RestMethod -Method Put -Uri ($api + $fileName) -Headers $hdr -ContentType "application/json" `
            -Body (@{ message = "Import-Report $stamp"; content = $b64 } | ConvertTo-Json) | Out-Null
        $sha = $null
        try { $sha = (Invoke-RestMethod -Uri ($api + "latest.md") -Headers $hdr).sha } catch {}
        $body = @{ message = "Import-Report latest $stamp"; content = $b64 }
        if ($sha) { $body["sha"] = $sha }
        Invoke-RestMethod -Method Put -Uri ($api + "latest.md") -Headers $hdr -ContentType "application/json" `
            -Body ($body | ConvertTo-Json) | Out-Null
        Write-Output "Report zu GitHub hochgeladen: reports/import/$fileName"
    } catch {
        Write-Output ("GitHub-Upload fehlgeschlagen: " + $_.Exception.Message)
    }
} else {
    Write-Output "Kein github.token - Report nur lokal."
}
