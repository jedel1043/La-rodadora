Proyecto de chatbot para mueso La Rodadora.

# Requisitos (Python)
- Python 3+
- kivymd
- kivy
- tensorflow
- keras
- numpy
- nltk
- TTS
- speechrecognition
- pyaudio

# Requisitos del sistema
- Poetry
- CUDA (si se requiere aceleración de GPU)
- Voces de texto a voz en español e inglés instaladas
- Powershell (sólo Windows)

Si se desea trabajar en Windows, se necesita ejecutar primero el
script `build.ps1` en la raíz del proyecto utilizando Powershell:

```powershell
.\build.ps1
```

# Ejecución
```
poetry install
poetry run python src/gui/main.py
```
