import asyncio
import os
import requests
import torch
from faster_whisper import WhisperModel
from TTS.api import TTS 
from moviepy import (
    VideoFileClip, AudioFileClip, TextClip, 
    CompositeVideoClip, ColorClip, CompositeAudioClip,
    concatenate_videoclips
)
import time
from tqdm import tqdm
# from moviepy.config import change_settings

# --- CONFIGURAÇÕES ---
PEXELS_API_KEY = "dVs9nwJTlR5sTo1m6CaBdrtAJinw72jWpHvexUKpDIwLgV0YcUUToMOv" 
OUTPUT_FILENAME = "video_xtts_music.mp4"
SPEAKER_WAV = "ref_voice.wav" # ARQUIVO OBRIGATÓRIO (Voz para clonar)

# Sistema avançado de detecção de GPU
def detect_gpu_optimization():
    if not torch.cuda.is_available():
        return "cpu", "int8", 4
    
    gpu_name = torch.cuda.get_device_name(0).upper()
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3  # GB
    
    print(f"🎮 GPU Detectada: {gpu_name}")
    print(f"💾 Memória VRAM: {gpu_memory:.1f} GB")
    
    # Otimização específica para cada GPU
    if "GTX 1060" in gpu_name or "1060" in gpu_name:
        print("🚀 Otimizando para GTX 1060 (6GB)...")
        return "cuda", "float16", 6  # 6 threads para GTX 1060
    elif "RX 6600M" in gpu_name or "6600M" in gpu_name:
        print("🚀 Otimizando para RX 6600M (AMD)...")
        return "cuda", "float16", 8  # 8 threads para RX 6600M
    elif "RTX 5070" in gpu_name or "5070" in gpu_name:
        print("🚀 Otimizando para RTX 5070 (12GB)...")
        return "cuda", "float16", 12  # 12 threads para RTX 5070
    elif "RTX" in gpu_name:
        print("🚀 Otimizando para RTX Genérica...")
        return "cuda", "float16", 8
    else:
        print("🚀 Usando configuração padrão GPU...")
        return "cuda", "float16", 6

DEVICE, COMPUTE_TYPE, THREADS = detect_gpu_optimization()

# Se der erro de ImageMagick, descomente:
# change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"})

class XTTSVideoBot:
    def __init__(self):
        print(f"🚀 Inicializando Bot XTTS + Música em: {DEVICE.upper()}")
        
        # 1. Carregar XTTS
        try:
            # Patch input to auto-accept license
            import builtins
            original_input = builtins.input
            builtins.input = lambda prompt="": "y"
            
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(DEVICE)
            
            # Restore original input
            builtins.input = original_input
        except Exception as e:
            print(f"❌ Erro XTTS: {e}")
            raise e

        # 2. Carregar Whisper
        self.whisper = WhisperModel("small", device=DEVICE, compute_type=COMPUTE_TYPE)

        self.width = 1080
        self.height = 1920

    def generate_audio_xtts(self, text, filename="temp_voice.wav"):
        if not os.path.exists(SPEAKER_WAV):
            raise FileNotFoundError(f"⚠️ Faltando arquivo '{SPEAKER_WAV}' para clonagem!")
            
        print(f"🎙️  Clonando voz...")
        with tqdm(total=100, desc="🎙️ Gerando Voz XTTS", unit="%") as pbar:
            # Simulação de progresso para TTS
            for i in range(10):
                time.sleep(0.5)
                pbar.update(10)
            
            # Adicionei speed=1.1 para ficar um pouco mais dinâmico
            self.tts.tts_to_file(
                text=text,
                file_path=filename,
                speaker_wav=SPEAKER_WAV,
                language="pt",
                split_sentences=True,
                speed=1.1 
            )
            pbar.update(0)  # Completa
        return filename

    def get_music(self, filename="background_music.mp3"):
        """Baixa música se não existir, ou usa uma local"""
        if os.path.exists(filename):
            return filename
            
        print("🎵 Baixando música Lo-Fi (Royalty Free)...")
        # URL exemplo de música livre (Chad Crouch - Algorithms)
        url = "https://files.freemusicarchive.org/storage-freemusicarchive-org/music/ccCommunity/Chad_Crouch/Arps/Chad_Crouch_-_Algorithms.mp3"
        try:
            r = requests.get(url)
            with open(filename, 'wb') as f:
                f.write(r.content)
            return filename
        except Exception as e:
            print(f"⚠️ Erro ao baixar música: {e}")
            return None

    def get_word_timestamps(self, audio_path):
        print("📝 Transcrevendo...")
        with tqdm(total=100, desc="📝 Transcrevendo Áudio", unit="%") as pbar:
            segments, _ = self.whisper.transcribe(audio_path, word_timestamps=True)
            pbar.update(50)
            
            word_data = []
            for segment in segments:
                for word in segment.words:
                    word_data.append({
                        "word": word.word.strip(),
                        "start": word.start,
                        "end": word.end
                    })
            pbar.update(50)
        return word_data

    def download_bg(self, query, filename="temp_bg.mp4"):
        print(f"🎬 Buscando visual '{query}'...")
        headers = {'Authorization': PEXELS_API_KEY}
        url = f"https://api.pexels.com/videos/search?query={query}&orientation=portrait&per_page=3"
        try:
            r = requests.get(url, headers=headers)
            if not r.json().get('videos'): return None
            # Tenta pegar video HD
            video_files = r.json()['videos'][0]['video_files']
            best = next((v for v in video_files if v['width'] >= 720), video_files[0])
            
            with requests.get(best['link'], stream=True) as s:
                with open(filename, 'wb') as f:
                    for chunk in s.iter_content(chunk_size=8192): f.write(chunk)
            return filename
        except: return None

    def create_captions(self, word_data):
        print("✨ Renderizando legendas dinâmicas...")
        clips = []
        
        for item in word_data:
            word = item['word']
            dur = item['end'] - item['start']
            if dur < 0.1: dur = 0.1

            try:
                txt = (TextClip(
                        text=word.upper(), 
                        font_size=90, 
                        color='#FFD700',  # Dourado como no HeavyDutyBot
                        stroke_color='black', 
                        stroke_width=3
                       )
                       .with_position(('center', self.height * 0.7))  # 70% da altura (para cima)
                       .with_start(item['start'])
                       .with_duration(dur))
                clips.append(txt)
            except Exception as e:
                print(f"⚠️ Erro ao criar texto: {e}. Pulando palavra '{word}'")
                continue
                
        return clips

    def run(self, script, query):
        # 1. Gerar Voz
        voice_path = self.generate_audio_xtts(script)
        
        # 2. Dados de Legenda
        word_data = self.get_word_timestamps(voice_path)
        
        # 3. Baixar Video Background
        bg_path = self.download_bg(query)
        
        # --- MONTAGEM DE ÁUDIO (MIXAGEM) ---
        print("🎚️ Mixando áudio (Voz + Música)...")
        voice_clip = AudioFileClip(voice_path)
        music_path = self.get_music()
        
        final_audio = voice_clip
        
        if music_path:
            music_clip = AudioFileClip(music_path)
            
            # Acelerar música em 1.25x - ajustando a duração
            original_duration = music_clip.duration
            music_clip = music_clip.subclipped(0, original_duration / 1.25)
            
            # Loop da música para cobrir a voz inteira
            if music_clip.duration < voice_clip.duration:
                music_clip = music_clip.with_loop(duration=voice_clip.duration + 1)
            
            # Corta a música no tamanho exato da voz
            music_clip = music_clip.subclipped(0, voice_clip.duration)
            
            # DUCKING: Volume da música em 8% do original
            music_clip = music_clip.with_volume_scaled(0.08)
            
            # Combina
            final_audio = CompositeAudioClip([voice_clip, music_clip])

        # --- MONTAGEM DE VÍDEO ---
        if bg_path:
            video = VideoFileClip(bg_path)
        else:
            video = ColorClip((1080,1920), color=(0,0,0), duration=voice_clip.duration)
        
        # Loop video manualmente
        if video.duration < voice_clip.duration:
            # Calcula quantas repetições precisamos
            loops_needed = int(voice_clip.duration / video.duration) + 1
            video_clips = []
            for i in range(loops_needed):
                video_clips.append(video)
            video = concatenate_videoclips(video_clips)
        video = video.subclipped(0, voice_clip.duration)
        
        # Crop 9:16
        video = video.resized(height=1920)
        if video.w > 1080: video = video.crop(x1=video.w/2-540, width=1080, height=1920)
        
        # Seta o áudio mixado no vídeo
        video = video.with_audio(final_audio)
        
        # Adiciona legendas
        subs = self.create_captions(word_data)
        final = CompositeVideoClip([video] + subs)
        
        print("🎥 Renderizando (High Quality)...")
        with tqdm(total=100, desc="🎥 Renderizando Vídeo", unit="%") as pbar:
            final.write_videofile(
                OUTPUT_FILENAME, 
                fps=30, 
                codec='libx264', 
                audio_codec='aac', 
                preset='medium',
                threads=THREADS  # Usando threads otimizadas para cada GPU
            )
            pbar.update(100)
        
        # Limpeza
        try: 
            os.remove(voice_path)
            if bg_path: os.remove(bg_path)
        except: pass
        print(f"✅ Vídeo salvo com música: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    # Verificação de segurança
    if not os.path.exists(SPEAKER_WAV):
        print(f"❌ PARE! Você precisa colocar um arquivo '{SPEAKER_WAV}' na pasta (use 6s da sua voz ou de um narrador).")
    elif PEXELS_API_KEY == "SUA_API_KEY_AQUI":
        print("❌ Configure sua API Key da Pexels.")
    else:
        bot = XTTSVideoBot()
        
        roteiro = (
            "Você sabia que o DNA humano é 50% idêntico ao de uma banana? "
            "Isso não significa que somos meio banana, mas sim que compartilhamos as mesmas bases fundamentais da vida celular! "
            "A biologia é fascinante, não é?"
        )
        
        bot.run(roteiro, "dna helix loop")