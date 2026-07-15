param(
    [int]$Port = 8765,
    [int]$ReplayCount = 20
)

$ErrorActionPreference = 'Stop'
$server = $null
$sessions = @()
$fixtureRecords = @()

function Invoke-PlaywrightCli {
    param([string[]]$Arguments)
    $previousPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $output = & npx.cmd --yes --package '@playwright/cli' playwright-cli @Arguments 2>&1
        $exitCode = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $previousPreference
    }
    if ($exitCode -ne 0) {
        throw "playwright-cli failed: $($Arguments -join ' ')`n$output"
    }
    $text = ($output -join "`n")
    if ($text -match '### Error') {
        throw "playwright-cli reported an error: $($Arguments -join ' ')`n$text"
    }
    return $text
}

function Wait-ReferencePage {
    param([string]$Url)
    for ($attempt = 0; $attempt -lt 50; $attempt += 1) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 1
            if ($response.StatusCode -eq 200) { return }
        } catch {
        }
        Start-Sleep -Milliseconds 100
    }
    throw "layout reference server did not become ready: $Url"
}

try {
    $pythonExecutable = Join-Path $PWD '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $pythonExecutable)) {
        $pythonExecutable = (Get-Command python).Source
    }
    $server = Start-Process $pythonExecutable -ArgumentList @(
        '-X', 'utf8', '-m', 'tests._attempts.dartlabUniverse.visual.liveLayoutServer',
        '--port', "$Port"
    ) -WindowStyle Hidden -PassThru
    $url = "http://127.0.0.1:$Port/layoutReference.html"
    Wait-ReferencePage -Url $url
    $fixtureUrl = "http://127.0.0.1:$Port/liveLayoutFixtures.json"
    $parsedFixtures = (Invoke-WebRequest -Uri $fixtureUrl -UseBasicParsing).Content | ConvertFrom-Json
    foreach ($fixture in $parsedFixtures) {
        $fixtureRecords += $fixture
    }

    $browserNames = @('chrome', 'firefox', 'webkit')
    $measurements = @()
    foreach ($browser in $browserNames) {
        $session = "universe-v02-$browser"
        $sessions += $session
        Invoke-PlaywrightCli -Arguments @("-s=$session", 'open', $url, '--browser', $browser) | Out-Null
        Invoke-PlaywrightCli -Arguments @("-s=$session", 'resize', '1280', '720') | Out-Null
        $replayScript = @(
            'async page => {'
            'const results = [];'
            "const fixtures = await page.evaluate('window.__universeLayout.fixtures()');"
            'for (const fixture of fixtures) {'
            "for (let replay = 0; replay < $ReplayCount; replay += 1) {"
            'await page.reload();'
            "await page.waitForFunction('window.__universeLayout && window.__universeLayout.measure');"
            'const offset = replay % fixture.nodes.length;'
            'const orderedNodes = [...fixture.nodes.slice(offset), ...fixture.nodes.slice(0, offset)];'
            'if (replay % 2 === 1) orderedNodes.reverse();'
            "await page.evaluate('window.__universeLayout.setScene(' + JSON.stringify(orderedNodes) + ',' + JSON.stringify(fixture.sourceSceneHash) + ')');"
            "const measurement = await page.evaluate('window.__universeLayout.measure()');"
            'results.push({ ...measurement, sceneName: fixture.sceneName });'
            '}'
            '}'
            'return JSON.stringify(results);'
            '}'
        ) -join ' '
        $raw = Invoke-PlaywrightCli -Arguments @('--raw', "-s=$session", 'run-code', $replayScript)
        $trimmed = $raw.Trim()
        if ($trimmed.StartsWith('"') -and $trimmed.EndsWith('"')) {
            $trimmed = $trimmed | ConvertFrom-Json
        }
        $parsedMeasurements = $trimmed | ConvertFrom-Json
        $browserMeasurements = @()
        foreach ($entry in $parsedMeasurements) {
            $browserMeasurements += $entry
        }
        for ($replay = 0; $replay -lt $browserMeasurements.Count; $replay += 1) {
            $measurement = $browserMeasurements[$replay]
            $measurements += [pscustomobject]@{
                browser = $browser
                sceneName = $measurement.sceneName
                replay = $replay % $ReplayCount
                logicalHash = $measurement.logicalHash
                anchorHash = $measurement.anchorHash
                innerWidth = $measurement.innerWidth
                innerHeight = $measurement.innerHeight
                dpr = $measurement.dpr
                anchors = $measurement.anchors
            }
        }
        Invoke-PlaywrightCli -Arguments @("-s=$session", 'close') | Out-Null
        $sessions = @($sessions | Where-Object { $_ -ne $session })
    }

    $baselines = @{}
    $baselineAnchors = @{}
    foreach ($measurement in $measurements) {
        if (-not $baselines.ContainsKey($measurement.sceneName)) {
            $baselines[$measurement.sceneName] = $measurement
            $anchors = @{}
            foreach ($anchor in $measurement.anchors) { $anchors[$anchor.nodeId] = $anchor }
            $baselineAnchors[$measurement.sceneName] = $anchors
        }
    }
    $maxAnchorDriftPx = 0.0
    $logicalHashMatches = 0
    $anchorHashMatches = 0
    $viewportMatches = 0
    foreach ($measurement in $measurements) {
        $baseline = $baselines[$measurement.sceneName]
        if ($measurement.logicalHash -eq $baseline.logicalHash) { $logicalHashMatches += 1 }
        if ($measurement.anchorHash -eq $baseline.anchorHash) { $anchorHashMatches += 1 }
        if ($measurement.innerWidth -eq 1280 -and
            $measurement.innerHeight -eq 720 -and
            $measurement.dpr -eq $baseline.dpr) {
            $viewportMatches += 1
        }
        foreach ($anchor in $measurement.anchors) {
            $expected = $baselineAnchors[$measurement.sceneName][$anchor.nodeId]
            $drift = [Math]::Max([Math]::Abs($anchor.x - $expected.x), [Math]::Abs($anchor.y - $expected.y))
            if ($drift -gt $maxAnchorDriftPx) { $maxAnchorDriftPx = $drift }
        }
    }
    $expectedMeasurementCount = $browserNames.Count * $fixtureRecords.Count * $ReplayCount
    $report = [ordered]@{
        schemaVersion = 'browserLayoutAudit.v1'
        browsers = $browserNames
        browserCount = $browserNames.Count
        scenes = @($fixtureRecords | ForEach-Object { $_.sceneName })
        sceneCount = $fixtureRecords.Count
        replayCountPerBrowser = $ReplayCount
        measurementCount = $measurements.Count
        logicalHashMatches = $logicalHashMatches
        anchorHashMatches = $anchorHashMatches
        viewportAndDprMatches = $viewportMatches
        maxAnchorDriftPx = $maxAnchorDriftPx
        anchorDriftTargetPx = 1
        passed = $measurements.Count -eq $expectedMeasurementCount -and
            $logicalHashMatches -eq $measurements.Count -and
            $anchorHashMatches -eq $measurements.Count -and
            $viewportMatches -eq $measurements.Count -and
            $maxAnchorDriftPx -le 1
    }
    $report | ConvertTo-Json -Depth 8
    if (-not $report.passed) {
        throw "browser layout audit failed: $($report | ConvertTo-Json -Compress -Depth 8)"
    }
} finally {
    foreach ($session in $sessions) {
        try { Invoke-PlaywrightCli -Arguments @("-s=$session", 'close') | Out-Null } catch { }
    }
    try { Invoke-PlaywrightCli -Arguments @('close-all') | Out-Null } catch { }
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force -ErrorAction SilentlyContinue
        $server.WaitForExit(5000) | Out-Null
    }
}
