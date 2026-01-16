from django.urls import path
from .views import UserInteractionView

app_name = "like_app"

urlpatterns = [
    # POST /api/like/interaction/
    path('interaction/', UserInteractionView.as_view(), name='user_interaction'),
]