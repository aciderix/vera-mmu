param(
  [Parameter(Mandatory = $true)][string]$CandidateDirectory
)

$ErrorActionPreference = 'Stop'
$candidate = (Resolve-Path -LiteralPath $CandidateDirectory).Path
$manifestPath = Join-Path $candidate 'release-manifest.json'
$sumsPath = Join-Path $candidate 'SHA256SUMS'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf) -or -not (Test-Path -LiteralPath $sumsPath -PathType Leaf)) {
  throw 'Manifest ou SHA256SUMS final absent.'
}
$manifest = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
if ($manifest.format -ne 'vera-release-candidate/v1' -or $manifest.target -ne 'x86_64-pc-windows-msvc') {
  throw 'Manifest Windows inattendu.'
}
$expected = @{}
foreach ($artifact in $manifest.artifacts) {
  if ([IO.Path]::GetFileName($artifact.path) -ne $artifact.path -or $expected.ContainsKey($artifact.path)) { throw 'Nom de manifest ambigu.' }
  $path = Join-Path $candidate $artifact.path
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Asset absent : $($artifact.path)" }
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
  if ($hash -ne $artifact.sha256 -or (Get-Item -LiteralPath $path).Length -ne $artifact.size_bytes) { throw "Manifest invalide : $($artifact.path)" }
  $expected[$artifact.path] = $true
}
$expected['release-manifest.json'] = $true
$seen = @{}
foreach ($line in Get-Content -LiteralPath $sumsPath) {
  if ($line -notmatch '^([0-9a-f]{64})  ([^/\\]+)$') { throw 'SHA256SUMS final invalide.' }
  $hash = $Matches[1]; $name = $Matches[2]
  if ($name -eq 'SHA256SUMS' -or -not $expected.ContainsKey($name) -or $seen.ContainsKey($name)) { throw 'SHA256SUMS hors périmètre.' }
  if ((Get-FileHash -LiteralPath (Join-Path $candidate $name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $hash) { throw "Checksum invalide : $name" }
  $seen[$name] = $true
}
if ($seen.Count -ne $expected.Count) { throw 'SHA256SUMS incomplet.' }

function Assert-Starts([string]$Executable, [string]$Label) {
  $process = Start-Process -FilePath $Executable -PassThru
  try {
    Start-Sleep -Seconds 8
    if ($process.HasExited) { throw "$Label s’est arrêté prématurément : $($process.ExitCode)" }
  } finally {
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force; $process.WaitForExit() }
  }
}

$temp = Join-Path $env:RUNNER_TEMP ("vera-runtime-smoke-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force -Path $temp | Out-Null
try {
  $cliArchive = Get-ChildItem -LiteralPath $candidate -Filter 'vera-mmu-cli_*.zip' | Select-Object -First 1
  if ($null -eq $cliArchive) { throw 'Archive CLI Windows absente.' }
  $cliDir = Join-Path $temp 'cli'; Expand-Archive -LiteralPath $cliArchive.FullName -DestinationPath $cliDir -Force
  $cli = Join-Path $cliDir 'vmmu.exe'
  if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) { throw 'vmmu.exe absent de l’archive.' }
  & $cli --help | Out-Null
  if ($LASTEXITCODE -ne 0) { throw 'La CLI Windows ne répond pas à --help.' }
  $project = Join-Path $temp 'project'; New-Item -ItemType Directory -Force -Path $project | Out-Null
  Set-Content -LiteralPath (Join-Path $project 'README.md') -Value 'runtime smoke only'
  $scan = (& $cli scan $project) | ConvertFrom-Json
  if ($LASTEXITCODE -ne 0 -or -not $scan.ok -or $scan.scan.status -ne 'OBSERVED' -or (Test-Path -LiteralPath (Join-Path $project '.vera-mmu'))) { throw 'Le scan CLI Windows n’est pas observationnel.' }

  $nsis = Get-ChildItem -LiteralPath $candidate -Filter '*-setup.exe' | Select-Object -First 1
  $nsisRoot = Join-Path $temp 'nsis'; $nsisProcess = Start-Process -FilePath $nsis.FullName -ArgumentList "/S", "/D=$nsisRoot" -Wait -PassThru
  if ($nsisProcess.ExitCode -ne 0) { throw "Installation NSIS refusée : $($nsisProcess.ExitCode)" }
  $nsisApp = Get-ChildItem -LiteralPath $nsisRoot -Filter 'VERA-MMU.exe' -File -Recurse | Select-Object -First 1
  if ($null -eq $nsisApp) { throw 'VERA-MMU.exe absent après installation NSIS.' }; Assert-Starts $nsisApp.FullName 'Application NSIS'

  $msi = Get-ChildItem -LiteralPath $candidate -Filter '*.msi' | Select-Object -First 1
  $msiRoot = Join-Path $temp 'msi'; $msiProcess = Start-Process -FilePath 'msiexec.exe' -ArgumentList "/i", $msi.FullName, "/qn", "INSTALLDIR=$msiRoot" -Wait -PassThru
  if ($msiProcess.ExitCode -notin 0, 3010) { throw "Installation MSI refusée : $($msiProcess.ExitCode)" }
  $msiApp = Get-ChildItem -LiteralPath $msiRoot -Filter 'VERA-MMU.exe' -File -Recurse | Select-Object -First 1
  if ($null -eq $msiApp) { throw 'VERA-MMU.exe absent après installation MSI.' }; Assert-Starts $msiApp.FullName 'Application MSI'
} finally {
  Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Output '{"ok":true,"target":"x86_64-pc-windows-msvc","checks":["integrity","cli-help","cli-observed-scan","nsis-install-start","msi-install-start"]}'
