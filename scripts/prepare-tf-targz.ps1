param (
    # VCS reposistory (github, gitlab, bitbucket,...)
    [Parameter(Mandatory = $true)][String]$RepositoryURL,
    # folder path to clone the repo into
    [Parameter()][String]$Path,
    # credential to authenticate the repo
    [Parameter()][SecureString]$Credential
)

# check if git installed on local machine
$isGitInstalled = $null -ne ( (Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*) + `
        (Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*) | `
        Where-Object { $null -ne $_.DisplayName -and $_.Displayname.Contains('Git') })
if ($isGitInstalled -eq $false) { Throw "Git is not installed on the system, exiting..." }
# if folder path provided, clone repo to that folder else clone to current path
if ($Path -eq $null) { $Path = ".\" }
# check if credential provided or not
# TODO: currently on 1 man operation so will leave this simple as possible to save effort
#if ($Credential -ne $null)
#{
#
#}
git clone $ReposistoryURL $Path