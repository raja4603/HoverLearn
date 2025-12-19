from django.db import models
from django.conf import settings

class Video(models.Model):
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='videos/')
    subtitle_file = models.FileField(upload_to='subs/') 
    thumbnail = models.ImageField(upload_to='thumbs/', blank=True, null=True)

    def __str__(self):
        return self.title

class SavedWord(models.Model):
    word = models.CharField(max_length=100)
    meaning = models.TextField()
    hindi = models.CharField(max_length=255, blank=True, null=True)     # Added
    synonyms = models.TextField(blank=True, null=True)                  # Added
    
    def __str__(self):
        return self.word

class DictionaryEntry(models.Model):
    """
    Acts as our permanent local dictionary.
    Stores data we fetched from NLTK/Google so we don't have to fetch it again.
    """
    word = models.CharField(max_length=100, unique=True, db_index=True)
    definition = models.TextField()
    hindi = models.CharField(max_length=255, blank=True, null=True)
    synonyms = models.TextField(blank=True, null=True) # Stored as "happy, joy, glee"
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.word


class VideoNote(models.Model):
    """Notes a user takes tied to a specific video and optional timestamp."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_notes')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    timestamp = models.FloatField(null=True, blank=True, help_text='Seconds into the video')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def formatted_timestamp(self):
        """Return timestamp as M:SS or None if no timestamp."""
        if self.timestamp is None:
            return None
        total = int(self.timestamp)
        mins = total // 60
        secs = total % 60
        return f"{mins}:{secs:02d}"

    def __str__(self):
        ts = f" @ {self.timestamp:.2f}s" if self.timestamp is not None else ""
        return f"Note by {self.user} on {self.video}{ts}"


class WatchHistory(models.Model):
    """Tracks per-user per-video last watched position."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watch_histories')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watch_histories')
    last_position = models.FloatField(default=0.0, help_text='Last known playback position in seconds')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} - {self.video} @ {self.last_position:.1f}s"