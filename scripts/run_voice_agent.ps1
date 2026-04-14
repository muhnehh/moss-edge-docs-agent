param(
    [Parameter(Mandatory = $true)]
    [string]$InputAudio,
    [string]$OutputAudio = "data/voice/answer.mp3",
    [switch]$NoTts
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path ".venv")) {
    py -m venv .venv
}

$python = ".\.venv\Scripts\python.exe"

if ($NoTts) {
    & $python -m agent.voice_agent --input-audio $InputAudio --no-tts
}
else {
    & $python -m agent.voice_agent --input-audio $InputAudio --output-audio $OutputAudio
}
