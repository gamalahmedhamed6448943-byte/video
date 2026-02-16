import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from gtts import gTTS
from moviepy.editor import *
from moviepy.config import change_settings
from PIL import Image, ImageFilter
import numpy as np
import uuid
import random
import nltk
import PIL.Image

# --- إعدادات النظام ---
if not hasattr(PIL.Image, 'ANTIALIAS'):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

try:
    if os.name == 'posix':
        change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})
except:
    pass

# تحميل الموارد مرة واحدة عند التشغيل
try:
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except:
    pass

# --- الدوال المساعدة ---

def generate_long_audio(text, lang='en', output_file='audio.mp3'):
    text = text.replace('"', '').replace("'", "").strip()
    sentences = text.split('. ')
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < 3000:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk)
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk)
        
    chunk_files = []
    audio_uid = uuid.uuid4().hex
    
    try:
        clips = []
        for i, chunk in enumerate(chunks):
            if not chunk.strip(): continue
            chunk_filename = f"temp_tts_{audio_uid}_{i}.mp3"
            tts = gTTS(text=chunk, lang=lang)
            tts.save(chunk_filename)
            chunk_files.append(chunk_filename)
            clips.append(AudioFileClip(chunk_filename))
            
        if clips:
            final_audio = concatenate_audioclips(clips)
            final_audio.write_audiofile(output_file, logger=None)
            final_audio.close()
            for clip in clips: clip.close()
            return True
    except Exception as e:
        print(f"Error audio: {e}")
        return False
    finally:
        for f in chunk_files:
            if os.path.exists(f): os.remove(f)
    return False

def get_best_image_url(img_tag, base_url):
    srcset = img_tag.get('srcset') or img_tag.get('data-srcset')
    if srcset:
        try:
            candidates = []
            for entry in srcset.split(','):
                parts = entry.strip().split()
                if len(parts) >= 1:
                    candidates.append((0, parts[0]))
            if candidates: return urljoin(base_url, candidates[0][1])
        except: pass
    src = img_tag.get('src') or img_tag.get('data-src')
    if src: return urljoin(base_url, src)
    return None

def extract_content(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        r = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, 'html.parser')
        
        for t in soup(['script', 'style', 'svg', 'footer', 'nav']): t.decompose()
        
        title = "News Video"
        h1 = soup.find('h1')
        if h1: title = h1.get_text(strip=True)
        else:
            t = soup.find('title')
            if t: title = t.get_text(strip=True).split('-')[0]
            
        target = soup.find('article') or soup.find('main') or soup
        paragraphs = target.find_all(['p', 'h2'])
        text_parts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30]
        full_text = ". ".join(text_parts)

        imgs = target.find_all('img')
        images = []
        seen = set()
        for img in imgs:
            u = get_best_image_url(img, url)
            if u and u not in seen:
                images.append(u)
                seen.add(u)
                
        return title, full_text, images
    except Exception as e:
        print(e)
        return None, None, []

def create_styled_clip(img_path, duration, screen_size=(1280, 720)):
    try:
        pil_img = Image.open(img_path).convert('RGB')
        bg_img = pil_img.resize(screen_size, Image.LANCZOS)
        bg_img = bg_img.filter(ImageFilter.GaussianBlur(radius=20))
        bg_clip = ImageClip(np.array(bg_img)).set_duration(duration)
        
        w, h = pil_img.size
        ratio = w / h
        new_h = int(screen_size[1] * 0.85)
        new_w = int(new_h * ratio)
        if new_w > screen_size[0]:
            new_w = int(screen_size[0] * 0.9)
            new_h = int(new_w / ratio)
            
        fg_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        fg_clip = ImageClip(np.array(fg_img)).set_duration(duration).set_position(('center', 'center'))
        
        return CompositeVideoClip([bg_clip, fg_clip], size=screen_size)
    except:
        return None

def process_video(url):
    session_uuid = uuid.uuid4().hex
    title, full_text, images = extract_content(url)
    
    if not full_text: return None, "No text found"
    
    audio_filename = f"audio_{session_uuid}.mp3"
    video_filename = f"video_{session_uuid}.mp4"
    
    if not generate_long_audio(f"{title}. {full_text}", output_file=audio_filename):
        return None, "Audio failed"
        
    audio_clip = AudioFileClip(audio_filename)
    total_duration = audio_clip.duration
    
    downloaded_imgs = []
    try:
        if images:
            clip_duration = max(3, total_duration / len(images))
            needed = int(total_duration / clip_duration) + 1
            images = images[:needed]
            
            for i, img_url in enumerate(images):
                try:
                    r = requests.get(img_url)
                    fname = f"img_{session_uuid}_{i}.jpg"
                    with open(fname, 'wb') as f: f.write(r.content)
                    downloaded_imgs.append(fname)
                except: pass
        
        clips = []
        if downloaded_imgs:
            real_duration = total_duration / len(downloaded_imgs)
            for img_path in downloaded_imgs:
                clip = create_styled_clip(img_path, real_duration)
                if clip: clips.append(clip)
                
        if clips:
            final_clip = concatenate_videoclips(clips, method="compose")
            if final_clip.duration > total_duration:
                final_clip = final_clip.subclip(0, total_duration)
        else:
            txt_clip = TextClip(title, fontsize=50, color='white', size=(1280, 720), method='caption')
            final_clip = txt_clip.set_duration(total_duration)

        final_clip = final_clip.set_audio(audio_clip)
        final_clip.write_videofile(video_filename, fps=1, codec="libx264", audio_codec="aac", preset="ultrafast", logger=None)
        
        audio_clip.close()
        final_clip.close()
        if os.path.exists(audio_filename): os.remove(audio_filename)
        for f in downloaded_imgs: os.remove(f)
        
        return video_filename, "Success"
        
    except Exception as e:
        return None, str(e)