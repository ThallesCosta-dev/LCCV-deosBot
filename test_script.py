#!/usr/bin/env python3
import sys
import os
import traceback

print("=== INICIANDO DIAGNÓSTICO ===")
print(f"Python: {sys.version}")
print(f"Diretório atual: {os.getcwd()}")

try:
    print("\n1. Testando imports básicos...")
    import requests
    import torch
    print("✅ Imports básicos OK")
    
    print("\n2. Testando faster-whisper...")
    from faster_whisper import WhisperModel
    print("✅ faster-whisper OK")
    
    print("\n3. Testando TTS...")
    from TTS.api import TTS
    print("✅ TTS import OK")
    
    print("\n4. Testando MoviePy...")
    from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ColorClip, CompositeAudioClip
    print("✅ MoviePy OK")
    
    print("\n5. Verificando arquivo de voz...")
    SPEAKER_WAV = "ref_voice.wav"
    if os.path.exists(SPEAKER_WAV):
        print(f"✅ Arquivo {SPEAKER_WAV} encontrado")
    else:
        print(f"❌ Arquivo {SPEAKER_WAV} NÃO encontrado")
    
    print("\n=== TODOS OS TESTES PASSARAM ===")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    print("\n=== TRACEBACK COMPLETO ===")
    traceback.print_exc()
