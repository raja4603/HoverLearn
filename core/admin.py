from django.contrib import admin
from .models import Video, SavedWord

# This makes the "Video" table appear in the admin panel
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'video_file', 'subtitle_file')

# This makes the "SavedWord" table appear
@admin.register(SavedWord)
class SavedWordAdmin(admin.ModelAdmin):
    list_display = ('word', 'meaning')