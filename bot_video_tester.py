import asyncio
import os
import requests
import edge_tts
from faster_whisper import WhisperModel
import moviepy

# Fix for PIL.Image.ANTIALIAS deprecation in newer Pillow versions
try:
    from PIL import Image
    if not hasattr(Image, 'ANTIALIAS'):
        Image.ANTIALIAS = Image.LANCZOS
except ImportError:
    pass

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

from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip, 
    CompositeVideoClip, ColorClip
)
from moviepy.audio.AudioClip import CompositeAudioClip
from moviepy.video.fx.all import speedx, resize

# --- CONFIGURAÇÕES ---
PEXELS_API_KEY = "dVs9nwJTlR5sTo1m6CaBdrtAJinw72jWpHvexUKpDIwLgV0YcUUToMOv" 
VOICE = "pt-BR-AntonioNeural" 
OUTPUT_FILENAME = "video_biologia_hd.mp4"
BGM_PATH = "background_music.mp3"  # Nome do seu arquivo de música

# Detecção de Hardware
DEVICE = "cuda" if os.environ.get('CUDA_VISIBLE_DEVICES') else "cpu"
COMPUTE_TYPE = "float16" if DEVICE == "cuda" else "int8"

class HeavyDutyBot:
    def __init__(self):
        print(f"🚀 Inicializando Bot Heavy Duty em: {DEVICE.upper()} ({COMPUTE_TYPE})")
        
        try:
            self.whisper_model = WhisperModel("small", device=DEVICE, compute_type=COMPUTE_TYPE)
        except Exception as e:
            print(f"⚠️ Erro ao carregar GPU: {e}. Mudando para CPU...")
            self.whisper_model = WhisperModel("small", device="cpu", compute_type="int8")

        self.width = 1080
        self.height = 1920

    async def generate_audio(self, text, filename="temp_voice.mp3"):
        print("🎙️ Gerando voz neural (Edge-TTS)...")
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(filename)
        return filename

    def get_word_timestamps(self, audio_path):
        print("📝 Transcrevendo áudio (Whisper)...")
        segments, _ = self.whisper_model.transcribe(audio_path, word_timestamps=True)
        
        word_data = []
        for segment in segments:
            for word in segment.words:
                word_data.append({
                    "word": word.word.strip(),
                    "start": word.start,
                    "end": word.end
                })
        return word_data

    def download_stock_video(self, query, filename="temp_bg.mp4"):
        print(f"🎬 Buscando vídeo no Pexels: '{query}'...")
        headers = {'Authorization': PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=3"
        
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
            
            if not data.get('videos'):
                return None
            
            video_files = data['videos'][0]['video_files']
            best_video = next((v for v in video_files if v['width'] >= 1080), video_files[0])
            
            with requests.get(best_video['link'], stream=True) as stream:
                with open(filename, "wb") as f:
                    for chunk in stream.iter_content(chunk_size=8192):
                        f.write(chunk)
            return filename
        except Exception as e:
            print(f"❌ Erro Pexels: {e}")
            return None

    def create_dynamic_captions(self, word_data):
        print("✨ Renderizando legendas dinâmicas...")
        text_clips = []
        
        for item in word_data:
            word = item['word']
            duration = item['end'] - item['start']
            if duration < 0.1: duration = 0.1

            try:
                txt_clip = (TextClip(
                                word.upper(), 
                                fontsize=85,  # Reduzido para evitar corte
                                color='#FFD700', 
                                font='Arial',  # Fonte que suporta caracteres especiais
                                stroke_color='black', 
                                stroke_width=3,
                                method='label'  # Método melhor para renderização
                            )
                            .set_position(('center', self.height * 0.75))  # 75% da altura (mais para cima)
                            .set_start(item['start'])
                            .set_duration(duration))
            except Exception as e:
                print(f"⚠️ Erro ao criar texto: {e}. Pulando palavra '{word}'")
                continue
            
            text_clips.append(txt_clip)
        return text_clips

    def run(self, script_text, search_term):
        # 1. Pipeline de Áudio (Voz)
        loop = asyncio.get_event_loop_policy().get_event_loop()
        voice_path = loop.run_until_complete(self.generate_audio(script_text))
        
        # 2. Pipeline de Transcrição
        word_data = self.get_word_timestamps(voice_path)
        
        # 3. Preparação de Clipes de Áudio
        voice_clip = AudioFileClip(voice_path)
        
        try:
            print(f"🎵 Processando trilha sonora: {BGM_PATH} (1.25x)")
            bg_music = AudioFileClip(BGM_PATH)
            bg_music = bg_music.fx(speedx, 1.25) # Acelera a música
            bg_music = bg_music.volumex(0.02)     # Reduz volume para 3% (muito mais baixo)
            bg_music = bg_music.set_duration(voice_clip.duration) # Ajusta duração
            bg_music = bg_music.audio_fadeout(2)
            
            final_audio = CompositeAudioClip([voice_clip, bg_music])
        except Exception as e:
            print(f"⚠️ Erro na trilha: {e}. Usando apenas voz.")
            final_audio = voice_clip

        # 4. Pipeline de Vídeo
        bg_path = self.download_stock_video(search_term)
        if bg_path:
            video_clip = VideoFileClip(bg_path)
        else:
            video_clip = ColorClip(size=(self.width, self.height), color=(0,0,0), duration=voice_clip.duration)

        # Ajuste de Tempo e Escala do Vídeo
        if video_clip.duration < voice_clip.duration:
            video_clip = video_clip.loop(duration=voice_clip.duration)
        else:
            video_clip = video_clip.subclip(0, voice_clip.duration)
            
        video_clip = video_clip.resize(height=self.height)
        if video_clip.w > self.width:
            video_clip = video_clip.crop(x1=video_clip.w/2 - self.width/2, width=self.width, height=self.height)
            
        video_clip = video_clip.set_audio(final_audio)
        
        # 5. Composição de Legendas e Renderização
        captions = self.create_dynamic_captions(word_data)
        final_video = CompositeVideoClip([video_clip] + captions)
        
        print("🎥 Renderizando Arquivo Final...")
        final_video.write_videofile(
            OUTPUT_FILENAME, 
            fps=30, 
            codec='libx264', 
            audio_codec='aac',
            threads=8,
            preset='medium'
        )
        
        # Limpeza
        voice_clip.close()
        final_audio.close()
        try:
            os.remove(voice_path)
            if bg_path: os.remove(bg_path)
        except: pass
        print(f"✅ CONCLUÍDO! Vídeo salvo: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    bot = HeavyDutyBot()
    
    roteiro = (  
    "30 segundos de Biologia Louca com o BioDrops, do LCC!, história de hoje... "  
    "Um físico holandês chamado Andre Geim decidiu testar os limites da física em um anfíbio. Ele construiu um campo magnético extremamente forte e colocou uma rã viva dentro dele. A rã levitou no ar, graças ao diamagnetismo da água em seu corpo, que reagiu ao magnetismo e a empurrou para cima. Geim provou que até seres vivos podem desafiar a gravidade em condições extremas. Anos depois, ele ganhou o Nobel de verdade pelo grafeno, mas essa rã flutuante ainda é lendária."  
    )  
    
    bot.run(roteiro, "frog")