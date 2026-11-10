#Requires -Version 5.1
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [ValidateSet("Plan", "Apply", "Rollback")]
    [string]$Action = "Plan",
    [Parameter(Mandatory = $true)]
    [string]$ConfigPath
)

$ErrorActionPreference = "Stop"
$RulePrefix = "PF-Killswitch-"

function Read-Targets {
    param([string]$Path)
    $resolved = (Resolve-Path -LiteralPath $Path).Path
    $config = Get-Content -LiteralPath $resolved -Raw -Encoding UTF8 | ConvertFrom-Json
    if (-not $config.targets -or $config.targets.Count -eq 0) {
        throw "Config must contain a non-empty targets array."
    }
    $seen = @{}
    foreach ($target in $config.targets) {
        $name = [string]$target.name
        $program = [string]$target.program
        if ($name -notmatch '^[A-Za-z0-9_.-]{2,64}$') {
            throw "Invalid target name '$name'. Use 2-64 letters, digits, dot, underscore or hyphen."
        }
        if ($seen.ContainsKey($name)) { throw "Duplicate target name '$name'." }
        $seen[$name] = $true
        if (-not [System.IO.Path]::IsPathRooted($program)) {
            throw "Program path for '$name' must be absolute."
        }
        if ($Action -ne "Rollback" -and -not (Test-Path -LiteralPath $program -PathType Leaf)) {
            throw "Program for '$name' does not exist: $program"
        }
        [pscustomobject]@{
            Name = $name
            RuleName = "$RulePrefix$name"
            Program = $program
            AllowLan = [bool]$target.allowLan
        }
    }
}

function Assert-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "$Action requires an elevated Administrator PowerShell. Use Plan for a non-elevated preview."
    }
}

function Get-BlockedRanges {
    param([bool]$AllowLan)
    if ($AllowLan) {
        $v4 = @(
            "0.0.0.0-9.255.255.255",
            "11.0.0.0-126.255.255.255",
            "128.0.0.0-172.15.255.255",
            "172.32.0.0-192.167.255.255",
            "192.169.0.0-198.17.255.255",
            "198.20.0.0-255.255.255.255"
        )
    } else {
        $v4 = @(
            "0.0.0.0-126.255.255.255",
            "128.0.0.0-198.17.255.255",
            "198.20.0.0-255.255.255.255"
        )
    }
    return @($v4 + "::-ffff:ffff:ffff:ffff:ffff:ffff:ffff:ffff")
}

$targets = @(Read-Targets -Path $ConfigPath)

if ($Action -eq "Plan") {
    Write-Host "PLAN only: no firewall changes were made."
    foreach ($target in $targets) {
        Write-Host ("{0}: program={1}; allowLoopback=true; allowFakeIp=198.18.0.0/15; allowLan={2}; blockOtherIPv4=true; blockIPv6=true" -f
            $target.RuleName, $target.Program, $target.AllowLan)
    }
    Write-Host "Next: verify rollback, then run Apply in an elevated shell and test both proxy-online and proxy-stopped states."
    exit 0
}

Assert-Administrator

if ($Action -eq "Rollback") {
    foreach ($target in $targets) {
        if ($PSCmdlet.ShouldProcess($target.RuleName, "Remove Privacy Fortress firewall rule")) {
            Get-NetFirewallRule -DisplayName $target.RuleName -ErrorAction SilentlyContinue |
                Remove-NetFirewallRule -ErrorAction Stop
            Write-Host "Removed (if present): $($target.RuleName)"
        }
    }
    Write-Host "Rollback complete. Verify normal networking and that no required rule remains."
    exit 0
}

$created = @()
try {
    foreach ($target in $targets) {
        if (-not $PSCmdlet.ShouldProcess($target.RuleName, "Replace Privacy Fortress firewall rule")) {
            continue
        }
        Get-NetFirewallRule -DisplayName $target.RuleName -ErrorAction SilentlyContinue |
            Remove-NetFirewallRule -ErrorAction Stop
        $ranges = Get-BlockedRanges -AllowLan $target.AllowLan
        New-NetFirewallRule -DisplayName $target.RuleName -Direction Outbound -Action Block `
            -Protocol Any -Program $target.Program -RemoteAddress $ranges -Profile Any -Enabled True |
            Out-Null
        $created += $target.RuleName
        $rule = Get-NetFirewallRule -DisplayName $target.RuleName -ErrorAction Stop
        $actualProgram = ($rule | Get-NetFirewallApplicationFilter).Program
        if ($actualProgram -ne $target.Program) {
            throw "Read-back program path mismatch for $($target.RuleName)."
        }
        Write-Host "Applied and read back: $($target.RuleName)"
    }
    Write-Host "Apply complete. Now test proxy-online connectivity and proxy-stopped fail-closed behavior."
} catch {
    foreach ($ruleName in $created) {
        Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue |
            Remove-NetFirewallRule -ErrorAction SilentlyContinue
    }
    throw "Apply failed; newly created rules were removed to restore availability. $($_.Exception.Message)"
}
