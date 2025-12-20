import json
import os
import google.generativeai as genai
from functools import lru_cache 
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from .models import Video, SavedWord, DictionaryEntry, VideoNote, WatchHistory, VideoVote
import pysrt
import nltk
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from nltk.corpus import wordnet

# --- SETUP: Configure Gemini ---
# Use the key you provided
GEMINI_API_KEY = "AIzaSyCHlWLIiJXPyQIDOFX3c7B5zuEbKFlKl90"
genai.configure(api_key=GEMINI_API_KEY)
# Switch model to gemini-2.0-flash as per your key
model = genai.GenerativeModel("gemini-2.5-flash") 

# Load Custom JSON
json_path = os.path.join(settings.BASE_DIR, 'core', 'common_words.json')
try:
    with open(json_path, 'r', encoding='utf-8') as f:
        COMMON_DICT = json.load(f)
except FileNotFoundError:
    COMMON_DICT = {}

# --- HELPER FUNCTION ---
@lru_cache(maxsize=1000)
def fetch_word_data(word):
    """
    Priority: DB Cache -> Custom JSON -> Gemini API -> NLTK (Backup)
    """
    clean_word = ''.join(e for e in word if e.isalnum())
    upper_word = clean_word.upper()
    
    # 1. DATABASE CACHE
    cached_entry = DictionaryEntry.objects.filter(word=upper_word).first()
    if cached_entry:
        return {
            'definition': cached_entry.definition,
            'hindi': cached_entry.hindi,
            'synonyms': cached_entry.synonyms.split(',') if cached_entry.synonyms else [],
            'found': True
        }

    data = {
        'definition': "Definition not available.",
        'found': False,
        'synonyms': [],
        'hindi': None
    }

    # 2. CUSTOM JSON
    if upper_word in COMMON_DICT:
        data['definition'] = COMMON_DICT[upper_word]
        data['found'] = True
    
    else:
        # 3. GEMINI API
        try:
            prompt = (
                f"Define the word '{clean_word}' in simple English. "
                f"Also provide the Hindi translation and 3 synonyms. "
                f"Return ONLY a JSON object with keys: 'definition', 'hindi', 'synonyms' (list)."
            )
            
            response = model.generate_content(prompt)
            
            text_response = response.text.replace('```json', '').replace('```', '').strip()
            ai_data = json.loads(text_response)
            
            data['definition'] = ai_data.get('definition', 'No definition found.')
            data['hindi'] = ai_data.get('hindi', '')
            data['synonyms'] = ai_data.get('synonyms', [])
            data['found'] = True
            
        except Exception as e:
            print(f"Gemini 2.0 Error: {e}")
            # 4. NLTK FALLBACK
            if wordnet.synsets(clean_word):
                synsets = wordnet.synsets(clean_word)
                data['definition'] = synsets[0].definition()
                data['found'] = True
                
                raw_synonyms = []
                for syn in synsets[:3]:
                    for lemma in syn.lemmas():
                        name = lemma.name().replace('_', ' ')
                        if name.lower() != clean_word.lower():
                            raw_synonyms.append(name)
                data['synonyms'] = list(set(raw_synonyms))[:5]

    # SAVE TO DB
    if data['found']:
        DictionaryEntry.objects.update_or_create(
            word=upper_word,
            defaults={
                'definition': data['definition'],
                'hindi': data['hindi'],
                'synonyms': ",".join(data['synonyms'])
            }
        )
            
    return data

# --- VIEWS ---

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def home(request):
    q = request.GET.get('q', '').strip()
    if q:
        videos = Video.objects.filter(title__icontains=q)
    else:
        videos = Video.objects.all()
    return render(request, 'home.html', {'videos': videos, 'q': q})

@login_required(login_url='login')
def watch_video(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    try:
        subs = pysrt.open(video.subtitle_file.path)
    except:
        subs = []

    subtitle_data = []
    for sub in subs:
        start_seconds = sub.start.hours * 3600 + sub.start.minutes * 60 + sub.start.seconds + sub.start.milliseconds / 1000.0
        end_seconds = sub.end.hours * 3600 + sub.end.minutes * 60 + sub.end.seconds + sub.end.milliseconds / 1000.0
        subtitle_data.append({
            'start': start_seconds,
            'end': end_seconds,
            'words': sub.text.split()
        })

    notes = VideoNote.objects.filter(user=request.user, video=video).order_by('-created_at')
    wh = WatchHistory.objects.filter(user=request.user, video=video).first()
    last_position = wh.last_position if wh else 0.0

    # Accept explicit jump timestamp via ?t=seconds
    jump_timestamp = None
    t_param = request.GET.get('t')
    if t_param:
        try:
            jump_timestamp = float(t_param)
        except (ValueError, TypeError):
            jump_timestamp = None

    # --- VOTE LOGIC (Fixing persistence issue) ---
    user_vote_obj = VideoVote.objects.filter(user=request.user, video=video).first()
    vote_type = user_vote_obj.vote if user_vote_obj else None
    
    likes = VideoVote.objects.filter(video=video, vote='LIKE').count()
    dislikes = VideoVote.objects.filter(video=video, vote='DISLIKE').count()

    return render(request, 'player.html', {
        'video': video,
        'subtitles': subtitle_data,
        'notes': notes,
        'last_position': last_position,
        'jump_timestamp': jump_timestamp,
        'vote_type': vote_type, # Passes user's choice to template
        'likes': likes,         # Passes total likes
        'dislikes': dislikes    # Passes total dislikes
    })

def get_definition(request, word):
    data = fetch_word_data(word)
    context = {
        'word': word,
        'definition': data['definition'],
        'hindi': data['hindi'],
        'synonyms': data['synonyms'],
        'found': data['found']
    }
    return render(request, 'partials/word_card.html', context)

def save_word(request, word):
    data = fetch_word_data(word)
    SavedWord.objects.update_or_create(
        word=word, 
        defaults={'meaning': data['definition'], 'hindi': data['hindi'], 'synonyms': ",".join(data['synonyms'])} 
    )
    return HttpResponse("<button style='width:100%; background:#46d369; color:white; border:none; padding:10px; border-radius:4px; font-weight:bold; cursor:default;'>Saved ✓</button>")


@login_required(login_url='login')
def saved_list(request):
    words = SavedWord.objects.all().order_by('-id') 
    notes = VideoNote.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'saved_list.html', {'words': words, 'notes': notes})

def delete_word(request, word_id):
    word = get_object_or_404(SavedWord, id=word_id)
    word.delete()
    return HttpResponse("")


@login_required(login_url='login')
@require_POST
def delete_note(request, note_id):
    note = get_object_or_404(VideoNote, id=note_id, user=request.user)
    note.delete()
    return HttpResponse("")


@login_required(login_url='login')
@require_POST
def save_note(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    content = request.POST.get('content', '').strip()
    timestamp = request.POST.get('timestamp', '').strip()
    if not content:
        return HttpResponseBadRequest('Missing note content')

    ts = None
    try:
        ts = float(timestamp) if timestamp else None
    except (ValueError, TypeError):
        ts = None

    VideoNote.objects.create(user=request.user, video=video, content=content, timestamp=ts)

    notes = VideoNote.objects.filter(user=request.user, video=video).order_by('-created_at')
    return render(request, 'partials/video_notes_list.html', {'notes': notes})


@login_required(login_url='login')
@require_POST
def update_history(request):
    video_id = request.POST.get('video_id') or ''
    current_time = request.POST.get('current_time') or ''

    try:
        video_id = int(video_id)
        current_time = float(current_time)
    except (ValueError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'invalid parameters'}, status=400)

    video = get_object_or_404(Video, id=video_id)

    wh, created = WatchHistory.objects.update_or_create(
        user=request.user,
        video=video,
        defaults={'last_position': current_time}
    )

    return JsonResponse({'status': 'ok', 'last_position': wh.last_position})

# Backwards compatibility alias
update_progress = update_history

@login_required(login_url='login')
def handle_vote(request, video_id, vote_type):
    if request.method == "POST":
        video = get_object_or_404(Video, id=video_id)
        
        existing_vote = VideoVote.objects.filter(user=request.user, video=video).first()
        
        current_vote = None
        if existing_vote:
            if existing_vote.vote == vote_type:
                # Toggle OFF
                existing_vote.delete()
            else:
                # Switch vote
                existing_vote.vote = vote_type
                existing_vote.save()
                current_vote = vote_type
        else:
            # Create new vote
            VideoVote.objects.create(user=request.user, video=video, vote=vote_type)
            current_vote = vote_type
            
        likes = VideoVote.objects.filter(video=video, vote='LIKE').count()
        dislikes = VideoVote.objects.filter(video=video, vote='DISLIKE').count()
        
        return render(request, 'partials/vote_buttons.html', {
            'video': video,
            'vote_type': current_vote,
            'likes': likes,
            'dislikes': dislikes
        })