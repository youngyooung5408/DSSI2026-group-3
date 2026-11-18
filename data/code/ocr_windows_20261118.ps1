# Windows built-in OCR (Windows.Media.Ocr, zh-Hant-TW) for every PNG in a folder.
# Usage: powershell -ExecutionPolicy Bypass -File data/code/ocr_windows_20261118.ps1 <png_dir> <out_json>
# Output: JSON object {png file name: [ {text, x, y, w, h} per recognized line ]}.
# Nothing leaves this computer; the OCR engine is part of Windows.
param([string]$InDir, [string]$OutJson)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$type) {
    $task = $asTaskGeneric.MakeGenericMethod($type).Invoke($null, @($op))
    $task.Wait(-1) | Out-Null
    $task.Result
}
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime] | Out-Null
[Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime] | Out-Null
[Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime] | Out-Null
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage((New-Object Windows.Globalization.Language 'zh-Hant-TW'))
if ($null -eq $engine) { throw 'zh-Hant-TW OCR engine unavailable' }
$out = [ordered]@{}
foreach ($f in Get-ChildItem -Path $InDir -Filter *.png | Sort-Object Name) {
    $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName)) ([Windows.Storage.StorageFile])
    $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
    $lines = @()
    foreach ($line in $result.Lines) {
        $r = $line.Words | ForEach-Object { $_.BoundingRect }
        $x = ($r | Measure-Object -Property X -Minimum).Minimum
        $y = ($r | Measure-Object -Property Y -Minimum).Minimum
        $lines += [ordered]@{ text = $line.Text; x = [int]$x; y = [int]$y }
    }
    $out[$f.Name] = $lines
    $stream.Dispose()
}
$out | ConvertTo-Json -Depth 5 | Out-File -FilePath $OutJson -Encoding utf8
