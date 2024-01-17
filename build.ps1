# Wheel name
$wheel = "triton-2.1.0-cp311-cp311-win_amd64.whl"

# Wheel URL to triton ZIP
$url = "https://nightly.link/wkpark/triton/actions/runs/7518654030/triton-dist%20windows-latest.zip"

# Temp file for zipped 
$tmp = New-TemporaryFile | Rename-Item -NewName { $_ -replace 'tmp$', 'zip' } -PassThru

# Temp folder for extraction
$tmpFolder = Join-Path $Env:Temp $(New-Guid)
New-Item -Type Directory -Path $tmpFolder | Out-Null

# Avoids unreasonably slow downloads when using `Invoke-WebRequest`
$ProgressPreference = 'SilentlyContinue'
Write-Host "Downloading zipped wheel to $tmp..."
Invoke-WebRequest $url -OutFile $tmp
Write-Host "Finished downloading wheel!"
$ProgressPreference = 'Continue'

Write-Host "Extracting wheel to $tmpFolder..."
Expand-Archive -Path $tmp -DestinationPath $tmpFolder
Write-Host "Finished extracting wheel!"

$srcFile = Join-Path $tmpFolder $wheel
$destFile = Join-Path $pwd.Path 'wheels' | Join-Path -ChildPath $wheel

Copy-Item $srcFile -Destination $destFile
