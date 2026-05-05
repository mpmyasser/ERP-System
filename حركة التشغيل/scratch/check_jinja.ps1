
$content = Get-Content "templates\cuts_entry_fixed.html" -Raw
$if_open = ([regex]::Matches($content, "{% if")).Count
$if_close = ([regex]::Matches($content, "{% endif %}")).Count
$for_open = ([regex]::Matches($content, "{% for")).Count
$for_close = ([regex]::Matches($content, "{% endfor %}")).Count
$block_open = ([regex]::Matches($content, "{% block")).Count
$block_close = ([regex]::Matches($content, "{% endblock %}")).Count

Write-Host "IF: $if_open / $if_close"
Write-Host "FOR: $for_open / $for_close"
Write-Host "BLOCK: $block_open / $block_close"
