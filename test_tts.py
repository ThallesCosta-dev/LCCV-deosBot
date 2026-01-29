#!/usr/bin/env python3
import os
import builtins

print("=== TESTANDO TTS ESPECIFICAMENTE ===")

try:
    print("1. Importando TTS...")
    from TTS.api import TTS
    print("✅ TTS importado")
    
    print("2. Patchando input para aceitar licença...")
    original_input = builtins.input
    builtins.input = lambda prompt="": "y"
    print("✅ Input patchado")
    
    print("3. Inicializando TTS (pode demorar)...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    print("✅ TTS inicializado")
    
    print("4. Movendo para CPU...")
    tts = tts.to("cpu")
    print("✅ TTS movido para CPU")
    
    # Restaurando input
    builtins.input = original_input
    
    print("=== TTS FUNCIONANDO PERFEITAMENTE ===")
    
except Exception as e:
    print(f"❌ ERRO NO TTS: {e}")
    import traceback
    traceback.print_exc()
