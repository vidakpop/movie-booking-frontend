from django.urls import path
from .views import SignUpview,LoginView

urlpatterns = [
    path('signup/', SignUpview.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
]