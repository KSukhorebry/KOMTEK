from django.urls import path

from .views import CheckElementView, RefBookElementsView, RefBookListView

urlpatterns = [
    path('refbooks/', RefBookListView.as_view(), name='refbook-list'),
    path(
        'refbooks/<int:refbook_id>/elements',
        RefBookElementsView.as_view(),
        name='refbook-elements',
    ),
    path(
        'refbooks/<int:refbook_id>/check_element',
        CheckElementView.as_view(),
        name='refbook-check-element',
    ),
]