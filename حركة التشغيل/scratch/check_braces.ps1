
$content = Get-Content "templates\cuts_entry_fixed.html" -Raw
$open = ($content.ToCharArray() | Where-Object { $_ -eq '{' }).Count
$close = ($content.ToCharArray() | Where-Object { $_ -eq '}' }).Count
Write-Host "Open: $open, Close: $close"
