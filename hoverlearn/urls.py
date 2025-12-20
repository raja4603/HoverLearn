from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth URLs
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # Main URLs (Protected)
    path('', views.home, name='home'),
    path('watch/<int:video_id>/', views.watch_video, name='watch'),
    path('my-list/', views.saved_list, name='saved_list'),
    
    # API
    path('get-def/<str:word>/', views.get_definition, name='get_def'),
    path('save-word/<str:word>/', views.save_word, name='save_word'),
    path('delete-word/<int:word_id>/', views.delete_word, name='delete_word'),

    # Video-related endpoints
    path('video/<int:video_id>/save-note/', views.save_note, name='save_note'),
    path('note/<int:note_id>/delete/', views.delete_note, name='delete_note'),
    path('update-history/', views.update_history, name='update_history'),
    
    # Voting URL
    path('vote/<int:video_id>/<str:vote_type>/', views.handle_vote, name='handle_vote'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)