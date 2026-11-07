#requires -version 5.1
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Uninstall')][string]$Action = 'Install',
    [string]$GameRoot = $PSScriptRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Utf8 = New-Object System.Text.UTF8Encoding($false)
$ExpectedManifestHash = '@@MANIFEST_SHA256@@'

function Get-BytesHash([byte[]]$Bytes) {
    $algorithm = [System.Security.Cryptography.SHA256]::Create()
    try { return 'sha256:' + ([BitConverter]::ToString($algorithm.ComputeHash($Bytes))).Replace('-', '').ToLowerInvariant() }
    finally { $algorithm.Dispose() }
}

function Get-PathHash([string]$Path) {
    return Get-BytesHash ([System.IO.File]::ReadAllBytes($Path))
}

function Assert-NoLinks([string]$Path) {
    $item = [System.IO.Path]::GetFullPath($Path)
    while ($item) {
        if ([System.IO.File]::Exists($item) -or [System.IO.Directory]::Exists($item)) {
            $attributes = [System.IO.File]::GetAttributes($item)
            if (($attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw "Linked paths are not supported: $item"
            }
        }
        $parent = [System.IO.Path]::GetDirectoryName($item)
        if ($parent -eq $item) { break }
        $item = $parent
    }
}

function Join-Checked([string]$Root, [string]$Relative) {
    if (-not $Relative -or $Relative -match '[\\<>:"|?*\x00-\x1f]' -or $Relative.StartsWith('/')) {
        throw 'Unsafe relative path in patch metadata.'
    }
    foreach ($part in $Relative.Split('/')) {
        if ($part -in @('', '.', '..') -or $part.EndsWith('.') -or $part.EndsWith(' ') -or
            $part -match '^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(\.|$)') {
            throw 'Unsafe path component in patch metadata.'
        }
    }
    $fullRoot = [System.IO.Path]::GetFullPath($Root)
    $joined = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($fullRoot, $Relative.Replace('/', [System.IO.Path]::DirectorySeparatorChar)))
    $prefix = $fullRoot.TrimEnd([System.IO.Path]::DirectorySeparatorChar) + [System.IO.Path]::DirectorySeparatorChar
    if (-not $joined.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Patch path escapes its root.' }
    Assert-NoLinks $joined
    return $joined
}

function Ensure-Parent([string]$Path) {
    $parent = [System.IO.Path]::GetDirectoryName($Path)
    [System.IO.Directory]::CreateDirectory($parent) | Out-Null
}

function Write-Atomic([string]$Path, [byte[]]$Bytes) {
    Ensure-Parent $Path
    $temporary = $Path + '.fvn-' + [Guid]::NewGuid().ToString('N') + '.tmp'
    try {
        [System.IO.File]::WriteAllBytes($temporary, $Bytes)
        if ([System.IO.File]::Exists($Path)) { [System.IO.File]::Replace($temporary, $Path, [NullString]::Value) }
        else { [System.IO.File]::Move($temporary, $Path) }
    }
    finally { if ([System.IO.File]::Exists($temporary)) { [System.IO.File]::Delete($temporary) } }
}

function Save-State($State) {
    $json = $State | ConvertTo-Json -Depth 30
    Write-Atomic $StatePath ($Utf8.GetBytes($json))
}

function Build-Bytes([byte[]]$Source, $Replacements) {
    $stream = New-Object System.IO.MemoryStream
    try {
        [long]$cursor = 0
        foreach ($replacement in $Replacements) {
            [long]$start = $replacement.start
            [long]$end = $replacement.end
            if ($start -lt $cursor -or $end -lt $start -or $end -gt $Source.LongLength) { throw 'Invalid or overlapping byte replacement.' }
            $stream.Write($Source, [int]$cursor, [int]($start - $cursor))
            [byte[]]$insert = [Convert]::FromBase64String([string]$replacement.replacement_base64)
            $stream.Write($insert, 0, $insert.Length)
            $cursor = $end
        }
        $stream.Write($Source, [int]$cursor, [int]($Source.LongLength - $cursor))
        return ,$stream.ToArray()
    }
    finally { $stream.Dispose() }
}

function Preserve-Current([string]$Path, [string]$Relative, [string]$Category) {
    if ([System.IO.File]::Exists($Path)) {
        $destination = Join-Checked $BackupRoot ('removed/' + $Category + '/' + [Guid]::NewGuid().ToString('N') + '/' + $Relative)
        Ensure-Parent $destination
        [System.IO.File]::Move($Path, $destination)
    }
}

function Undo-Patch($State) {
    if ($State.manifest_sha256 -ne $ExpectedManifestHash -or $State.patch_id -ne $Patch.patch_id -or
        $State.game_root -ne $Root) { throw 'Backup state does not match this patch and game directory.' }
    if ($State.phase -notin @('prepared', 'installed', 'uninstalled')) { throw 'Unrecognized backup state.' }
    $expectedCompiled = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($file in $Patch.files) {
        $compiledPath = [System.IO.Path]::ChangeExtension([string]$file.path, '.rpyc').Replace('\', '/')
        $expectedCompiled.Add($compiledPath) | Out-Null
    }
    if (@($State.compiled).Count -ne $expectedCompiled.Count) { throw 'Compiled backup inventory differs from the patch.' }
    foreach ($compiled in $State.compiled) {
        if (-not $expectedCompiled.Remove([string]$compiled.path) -or
            ($compiled.original_sha256 -and $compiled.original_sha256 -notmatch '^sha256:[0-9a-f]{64}$')) {
            throw 'Invalid compiled backup inventory.'
        }
    }
    if ($State.phase -eq 'uninstalled') { Write-Host 'Patch already uninstalled.'; return }
    # Validate all scripts, extras and backups before restoring any file.
    foreach ($file in $Patch.files) {
        $path = Join-Checked $Root $file.path
        $backup = Join-Checked $BackupRoot ('original/' + $file.path)
        if (-not [System.IO.File]::Exists($backup) -or (Get-PathHash $backup) -ne $file.source_sha256) { throw "Original backup failed verification: $($file.path)" }
        if (-not [System.IO.File]::Exists($path)) { throw "Game script is missing: $($file.path)" }
        $currentHash = Get-PathHash $path
        if ($currentHash -ne $file.target_sha256 -and $currentHash -ne $file.source_sha256) {
            throw "Script changed after installation; restore was refused: $($file.path)"
        }
    }
    foreach ($extra in $Patch.extras) {
        $path = Join-Checked $Root $extra.path
        if ([System.IO.Directory]::Exists($path)) { throw "Extra path became a directory: $($extra.path)" }
        if ([System.IO.File]::Exists($path) -and (Get-PathHash $path) -ne $extra.sha256) {
            throw "Extra file changed after installation; restore was refused: $($extra.path)"
        }
    }
    foreach ($compiled in $State.compiled) {
        $backup = Join-Checked $BackupRoot ('original/' + $compiled.path)
        $path = Join-Checked $Root $compiled.path
        if ($compiled.original_sha256) {
            if ([System.IO.File]::Exists($backup)) {
                if ((Get-PathHash $backup) -ne $compiled.original_sha256) { throw "Compiled backup failed verification: $($compiled.path)" }
            }
            elseif (-not [System.IO.File]::Exists($path) -or (Get-PathHash $path) -ne $compiled.original_sha256) {
                throw "Original compiled file is missing from game and backup: $($compiled.path)"
            }
        }
    }
    foreach ($file in $Patch.files) {
        $path = Join-Checked $Root $file.path
        $backup = Join-Checked $BackupRoot ('original/' + $file.path)
        if ((Get-PathHash $path) -ne $file.source_sha256) { Write-Atomic $path ([System.IO.File]::ReadAllBytes($backup)) }
    }
    foreach ($compiled in $State.compiled) {
        $path = Join-Checked $Root $compiled.path
        $backup = Join-Checked $BackupRoot ('original/' + $compiled.path)
        if ([System.IO.File]::Exists($backup) -or -not $compiled.original_sha256) {
            if ($compiled.original_sha256 -and [System.IO.File]::Exists($path) -and
                (Get-PathHash $path) -eq $compiled.original_sha256) { continue }
            Preserve-Current $path $compiled.path 'compiled'
            if ($compiled.original_sha256) { Write-Atomic $path ([System.IO.File]::ReadAllBytes($backup)) }
        }
    }
    foreach ($extra in $Patch.extras) {
        Preserve-Current (Join-Checked $Root $extra.path) $extra.path 'extras'
        # Ren'Py may have compiled a newly added runtime .rpy. Keep it in the backup.
        if ($extra.path.EndsWith('.rpy', [StringComparison]::OrdinalIgnoreCase)) {
            $compiledPath = [System.IO.Path]::ChangeExtension([string]$extra.path, '.rpyc').Replace('\', '/')
            Preserve-Current (Join-Checked $Root $compiledPath) $compiledPath 'extra-compiled'
        }
    }
    $State.phase = 'uninstalled'
    Save-State $State
    Write-Host "Original scripts restored. Backup retained at $BackupRoot"
}

$lock = $null
try {
    $Root = [System.IO.Path]::GetFullPath($GameRoot).TrimEnd([System.IO.Path]::DirectorySeparatorChar)
    Assert-NoLinks $Root
    if (-not [System.IO.Directory]::Exists((Join-Checked $Root 'game'))) { throw 'Choose the game EXE directory containing game/.' }
    $manifestPath = Join-Checked $PSScriptRoot 'patch.json'
    if ((Get-PathHash $manifestPath) -ne $ExpectedManifestHash) { throw 'patch.json does not match this installer.' }
    $Patch = [System.IO.File]::ReadAllText($manifestPath, $Utf8) | ConvertFrom-Json
    if ($Patch.schema -ne 'fvn-renpy-byte-delta/v1' -or $Patch.patch_id -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$') { throw 'Unsupported patch metadata.' }
    $guardNames = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($guard in $Patch.source_guards) {
        if (-not $guard.path.StartsWith('game/') -or -not $guard.path.EndsWith('.rpy', [StringComparison]::OrdinalIgnoreCase) -or -not $guardNames.Add([string]$guard.path)) { throw 'Duplicate or unsupported source guard path.' }
        Join-Checked $Root $guard.path | Out-Null
    }
    if (-not $guardNames.Count) { throw 'Patch has no source version guards.' }
    $names = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($file in $Patch.files) {
        if (-not $file.path.StartsWith('game/') -or -not $file.path.EndsWith('.rpy', [StringComparison]::OrdinalIgnoreCase) -or -not $names.Add([string]$file.path)) { throw 'Duplicate or unsupported script path.' }
        if (-not $guardNames.Contains([string]$file.path)) { throw 'Changed script has no source version guard.' }
        Join-Checked $Root $file.path | Out-Null
        $compiledPath = [System.IO.Path]::ChangeExtension([string]$file.path, '.rpyc').Replace('\', '/')
        if (-not $names.Add($compiledPath)) { throw 'Compiled path collision.' }
    }
    foreach ($extra in $Patch.extras) {
        if (-not $extra.path.StartsWith('game/') -or -not $names.Add([string]$extra.path)) { throw 'Duplicate extra path.' }
        Join-Checked $Root $extra.path | Out-Null
        Join-Checked $PSScriptRoot $extra.payload_path | Out-Null
        if ($extra.path.EndsWith('.rpy', [StringComparison]::OrdinalIgnoreCase)) {
            $compiledPath = [System.IO.Path]::ChangeExtension([string]$extra.path, '.rpyc').Replace('\', '/')
            if (-not $names.Add($compiledPath)) { throw 'Extra compiled path collision.' }
        }
    }
    $RuntimeGuards = @()
    if ($Patch.PSObject.Properties.Name -contains 'runtime_guards') { $RuntimeGuards = @($Patch.runtime_guards) }
    $runtimeNames = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    foreach ($guard in $RuntimeGuards) {
        if (-not $runtimeNames.Add([string]$guard.path) -or $guardNames.Contains([string]$guard.path) -or $names.Contains([string]$guard.path)) { throw 'Runtime guard duplicates or overlaps a writable/source path.' }
        if ($Action -eq 'Install') {
            $runtimePath = Join-Checked $Root $guard.path
            if (-not [System.IO.File]::Exists($runtimePath) -or ([System.IO.FileInfo]$runtimePath).Length -ne $guard.source_size -or
                (Get-PathHash $runtimePath) -ne $guard.source_sha256) { throw "Runtime version/platform mismatch: $($guard.path)" }
        }
    }
    $lockPath = Join-Checked $Root '.fvn-patch.lock'
    $lock = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    $BackupRoot = Join-Checked $Root ('.fvn-backups/' + $Patch.patch_id)
    $StatePath = Join-Checked $BackupRoot 'state.json'
    if ($Action -eq 'Uninstall') {
        if (-not [System.IO.File]::Exists($StatePath)) { throw 'No backup state found. Automatic restore cannot proceed. Preserve any backup directory; use a fresh official game copy if backup preparation was interrupted.' }
        $State = [System.IO.File]::ReadAllText($StatePath, $Utf8) | ConvertFrom-Json
        Undo-Patch $State
        exit 0
    }
    if ([System.IO.Directory]::Exists($BackupRoot) -or [System.IO.File]::Exists($BackupRoot)) {
        if ([System.IO.File]::Exists($StatePath)) {
            $previous = [System.IO.File]::ReadAllText($StatePath, $Utf8) | ConvertFrom-Json
            if ($previous.phase -eq 'uninstalled') { throw "This patch was restored previously. Archive its retained backup directory outside the game before reinstalling: $BackupRoot" }
            throw "Backup directory already exists. Recover/uninstall the previous attempt first: $BackupRoot"
        }
        throw "Backup directory has no state.json. Preserve it and use a fresh official game copy, or verify/restore originals before archiving this directory and retrying: $BackupRoot"
    }
    # All payloads and all original hashes are checked before creating backups or replacing scripts.
    foreach ($guard in $Patch.source_guards) {
        $path = Join-Checked $Root $guard.path
        if (-not [System.IO.File]::Exists($path) -or ([System.IO.FileInfo]$path).Length -ne $guard.source_size -or
            (Get-PathHash $path) -ne $guard.source_sha256) { throw "Wrong version or changed source script: $($guard.path)" }
    }
    $Prepared = @()
    $Compiled = @()
    foreach ($file in $Patch.files) {
        $path = Join-Checked $Root $file.path
        if (-not [System.IO.File]::Exists($path)) { throw "Original script not found: $($file.path)" }
        [byte[]]$bytes = [System.IO.File]::ReadAllBytes($path)
        if ($bytes.LongLength -ne $file.source_size -or (Get-BytesHash $bytes) -ne $file.source_sha256) { throw "Wrong version or changed source script: $($file.path)" }
        [byte[]]$target = Build-Bytes $bytes $file.replacements
        if ($target.LongLength -ne $file.target_size -or (Get-BytesHash $target) -ne $file.target_sha256) { throw "Delta output verification failed: $($file.path)" }
        $Prepared += @{ path = [string]$file.path; bytes = $target }
        $compiledPath = [System.IO.Path]::ChangeExtension([string]$file.path, '.rpyc').Replace('\', '/')
        $compiledFull = Join-Checked $Root $compiledPath
        if ([System.IO.Directory]::Exists($compiledFull)) { throw 'Compiled file path is a directory.' }
        $compiledHash = $null
        if ([System.IO.File]::Exists($compiledFull)) { $compiledHash = Get-PathHash $compiledFull }
        $Compiled += @{ path = $compiledPath; original_sha256 = $compiledHash }
    }
    foreach ($extra in $Patch.extras) {
        $destination = Join-Checked $Root $extra.path
        if ([System.IO.File]::Exists($destination) -or [System.IO.Directory]::Exists($destination)) { throw "Extra destination already exists: $($extra.path)" }
        $payload = Join-Checked $PSScriptRoot $extra.payload_path
        if (-not [System.IO.File]::Exists($payload) -or ([System.IO.FileInfo]$payload).Length -ne $extra.size -or (Get-PathHash $payload) -ne $extra.sha256) { throw "Extra payload verification failed: $($extra.path)" }
        if ($extra.path.EndsWith('.rpy', [StringComparison]::OrdinalIgnoreCase)) {
            $compiledPath = [System.IO.Path]::ChangeExtension([string]$extra.path, '.rpyc').Replace('\', '/')
            $compiledFull = Join-Checked $Root $compiledPath
            if ([System.IO.File]::Exists($compiledFull) -or [System.IO.Directory]::Exists($compiledFull)) { throw 'New runtime script already has a compiled file in the game.' }
        }
    }
    try {
        [System.IO.Directory]::CreateDirectory($BackupRoot) | Out-Null
        foreach ($file in $Patch.files) {
            $path = Join-Checked $Root $file.path
            $backup = Join-Checked $BackupRoot ('original/' + $file.path)
            Ensure-Parent $backup
            [System.IO.File]::Copy($path, $backup, $false)
            if ((Get-PathHash $backup) -ne $file.source_sha256 -or (Get-PathHash $path) -ne $file.source_sha256) { throw 'Source changed while preparing its backup.' }
        }
        $State = [PSCustomObject]@{ patch_id = $Patch.patch_id; manifest_sha256 = $ExpectedManifestHash; game_root = $Root; phase = 'prepared'; compiled = @($Compiled) }
        Save-State $State
    }
    catch {
        throw "Backup preparation failed before this installer replaced any game script or moved any compiled file. Preserve partial backups at $BackupRoot. $($_.Exception.Message)"
    }
    try {
        foreach ($compiled in $Compiled) {
            if ($compiled.original_sha256) {
                $path = Join-Checked $Root $compiled.path
                if ((Get-PathHash $path) -ne $compiled.original_sha256) { throw 'Compiled source changed while preparing installation.' }
                $backup = Join-Checked $BackupRoot ('original/' + $compiled.path)
                Ensure-Parent $backup
                [System.IO.File]::Move($path, $backup)
            }
        }
        foreach ($file in $Prepared) {
            $path = Join-Checked $Root $file.path
            $metadata = @($Patch.files | Where-Object { $_.path -eq $file.path })[0]
            if ((Get-PathHash $path) -ne $metadata.source_sha256) { throw 'Source changed immediately before replacement.' }
            Write-Atomic $path $file.bytes
        }
        foreach ($extra in $Patch.extras) {
            $path = Join-Checked $Root $extra.path
            if ([System.IO.File]::Exists($path) -or [System.IO.Directory]::Exists($path)) { throw 'Extra destination appeared during installation.' }
            Write-Atomic $path ([System.IO.File]::ReadAllBytes((Join-Checked $PSScriptRoot $extra.payload_path)))
        }
        foreach ($file in $Patch.files) {
            if ((Get-PathHash (Join-Checked $Root $file.path)) -ne $file.target_sha256) { throw 'Installed script failed final verification.' }
        }
        foreach ($extra in $Patch.extras) {
            if ((Get-PathHash (Join-Checked $Root $extra.path)) -ne $extra.sha256) { throw 'Installed extra failed final verification.' }
        }
        $State.phase = 'installed'
        Save-State $State
    }
    catch {
        $failure = $_
        try { Undo-Patch $State }
        catch { Write-Warning "Automatic restore could not finish. Preserve backup and state at $BackupRoot. $($_.Exception.Message)" }
        throw $failure
    }
    Write-Host "Patch installed. Original files are retained at $BackupRoot"
    Write-Host 'Start the game normally. Close it before running uninstall.cmd.'
}
catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
finally { if ($null -ne $lock) { $lock.Dispose() } }
