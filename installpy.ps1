$Url = "https://www.python.org/ftp/python/3.13.7/python-3.13.7-amd64.exe"
$Out = "$env:TEMP\python-3.13.7-amd64.exe"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Invoke-WebRequest -Uri $Url -OutFile $Out -UseBasicParsing
Start-Process -FilePath $Out
