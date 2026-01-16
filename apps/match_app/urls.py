# # apps/match_app/urls.py
# from django.urls import path

# urlpatterns = [
#     # Puedes dejarlo vacío por ahora, pero debe existir
# ]

# apps/match_app/urls.py

from django.urls import path
from .views import MatchRecommendationsView, CheckMatchView
from .views_refresh import RefreshImageURLsView, RefreshMatchImagesView

urlpatterns = [
    path(
        "recommendations/",
        MatchRecommendationsView.as_view(),
        name="match-recommendations",
    ),
    path(
        "refresh-images/",
        RefreshImageURLsView.as_view(),
        name="refresh-image-urls",
    ),
    path(
        "refresh-profile-images/",
        RefreshMatchImagesView.as_view(),
        name="refresh-profile-images",
    ),
    path(
        "check/<int:user_id>/",
        CheckMatchView.as_view(),
        name="check-match",
    ),
]

