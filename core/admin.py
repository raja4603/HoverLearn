from django.contrib import admin
from .models import Video, SavedWord

# This makes the "Video" table appear in the admin panel
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_description', 'video_file', 'subtitle_file')
    search_fields = ('title', 'description')

    def short_description(self, obj):
        return (obj.description[:60] + '...') if obj.description and len(obj.description) > 60 else obj.description
    short_description.short_description = 'Description'

# This makes the "SavedWord" table appear
@admin.register(SavedWord)
class SavedWordAdmin(admin.ModelAdmin):
    list_display = ('word', 'meaning')