# install_voice_env.ps1
# Windows helper: install pipwin, PyAudio and SpeechRecognition

Write-Host "Installing dependencies for voice input..."
try {
    python -m pip install --upgrade pip
    python -m pip install pipwin
    python -m pipwin install pyaudio
    python -m pip install SpeechRecognition
    Write-Host "Installation completed."
    exit 0
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    exit 1
}
