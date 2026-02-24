#!/usr/bin/env python3
"""
Test script to verify subtitle rendering with Portuguese special characters
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar caminho do ImageMagick para Windows
try:
    from moviepy.config import change_settings
    # Caminhos comuns para ImageMagick no Windows
    possible_paths = [
        r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick-7.1.0-Q16-HDRI\magick.exe",
        r"C:\Program Files (x86)\ImageMagick-7.1.1-Q16-HDRI\magick.exe",
        r"C:\Program Files\ImageMagick\magick.exe",
        r"C:\Program Files (x86)\ImageMagick\magick.exe"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            change_settings({"IMAGEMAGICK_BINARY": path})
            print(f"✅ ImageMagick encontrado em: {path}")
            break
    else:
        print("⚠️ ImageMagick não encontrado nos caminhos padrão")
except Exception as e:
    print(f"⚠️ Erro ao configurar ImageMagick: {e}")

from moviepy.editor import TextClip, ColorClip, CompositeVideoClip
import tempfile

def test_portuguese_subtitles():
    """Test rendering Portuguese special characters in subtitles"""
    print("🧪 Testando legendas com caracteres especiais...")
    
    # Test text with Portuguese special characters
    test_words = [
        "ação", "coração", "nação", "saudação",
        "é", "ê", "á", "à", "â", "ã", "ô", "õ", "ó", "ú", "ü", 
        "ç", "ñ", "¡", "¿",
        "biologia", "física", "química", "matemática",
        "Geim", "levitou", "magnético"
    ]
    
    clips = []
    width, height = 1080, 1920
    
    try:
        # Create background
        bg = ColorClip(size=(width, height), color=(0, 0, 0), duration=10)
        clips.append(bg)
        
        # Test each word
        for i, word in enumerate(test_words):
            try:
                txt = (TextClip(
                        word.upper(), 
                        fontsize=85,
                        color='#FFD700',
                        stroke_color='black', 
                        stroke_width=3,
                        font='Arial',
                        method='label'
                       )
                       .set_position(('center', height * 0.75))
                       .set_start(i * 0.5)
                       .set_duration(0.4))
                clips.append(txt)
                print(f"✅ Palavra '{word}' renderizada com sucesso")
            except Exception as e:
                print(f"❌ Erro ao renderizar '{word}': {e}")
        
        # Create test video
        if len(clips) > 1:
            final = CompositeVideoClip(clips)
            test_file = "test_subtitles.mp4"
            
            print(f"🎥 Renderizando vídeo de teste: {test_file}")
            final.write_videofile(
                test_file, 
                fps=30, 
                codec='libx264', 
                audio_codec='aac',
                preset='medium'
            )
            print(f"✅ Teste concluído! Vídeo salvo: {test_file}")
            
            # Cleanup
            try:
                os.remove(test_file)
                print("🧹 Arquivo de teste removido")
            except:
                pass
        else:
            print("❌ Nenhuma legenda foi criada para o teste")
            
    except Exception as e:
        print(f"❌ Erro geral no teste: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_portuguese_subtitles()
    if success:
        print("\n🎉 Teste de legendas concluído com sucesso!")
    else:
        print("\n💥 Teste falhou - verifique as configurações")
