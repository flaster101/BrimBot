$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
$env:JAVA_HOME = Join-Path $workspace '.tools/jdk/jdk-17.0.20.1+1'
$env:GRADLE_USER_HOME = Join-Path $workspace '.tools/gradle-home'
$signingPath = Join-Path $workspace '.tools/release-signing.json'
$keyPath = Join-Path $workspace '.tools/brimbot-release.jks'
if (-not (Test-Path -LiteralPath $signingPath)) {
    if (Test-Path -LiteralPath $keyPath) { throw 'Existing signing key has no password record; refusing to replace it.' }
    $bytes = New-Object byte[] 32
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    @{ password = [Convert]::ToBase64String($bytes) } | ConvertTo-Json | Set-Content -LiteralPath $signingPath
}
$signing = Get-Content -LiteralPath $signingPath -Raw | ConvertFrom-Json
$env:BRIMBOT_KEYSTORE = $keyPath
$env:BRIMBOT_STORE_PASSWORD = $signing.password
$env:BRIMBOT_KEY_PASSWORD = $signing.password
try {
    if (-not (Test-Path -LiteralPath $keyPath)) {
        & "$env:JAVA_HOME/bin/keytool.exe" -genkeypair -keystore $keyPath -alias brimbot -keyalg RSA -keysize 3072 -validity 10000 -dname 'CN=BrimBot, O=BrimBot' -storepass:env BRIMBOT_STORE_PASSWORD -keypass:env BRIMBOT_KEY_PASSWORD
        if ($LASTEXITCODE -ne 0) { throw 'Signing key creation failed' }
    }
    & "$workspace/.tools/gradle/gradle-8.11.1/bin/gradle.bat" -p "$workspace/android" :core:test :app:lintRelease :app:assembleRelease --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Release checks/build failed' }
    Copy-Item -LiteralPath "$workspace/android/app/build/outputs/apk/release/app-release.apk" -Destination "$workspace/artifacts/BrimBot.apk"
    & "$workspace/.tools/android-sdk/build-tools/35.0.0/apksigner.bat" verify --verbose --print-certs "$workspace/artifacts/BrimBot.apk"
    if ($LASTEXITCODE -ne 0) { throw 'APK signature verification failed' }
    Get-FileHash -LiteralPath "$workspace/artifacts/BrimBot.apk" -Algorithm SHA256
} finally {
    Remove-Item Env:BRIMBOT_STORE_PASSWORD,Env:BRIMBOT_KEY_PASSWORD -ErrorAction SilentlyContinue
}
