"""URL routes for the projects app, including nested stakeholder routes."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from projects.views import ProjectViewSet, StakeholderViewSet

router = DefaultRouter()
router.register(r"", ProjectViewSet, basename="project")

urlpatterns = [
    # Nested: /api/projects/{project_pk}/stakeholders/
    path(
        "<int:project_pk>/stakeholders/",
        StakeholderViewSet.as_view(
            {"get": "list", "post": "create"}
        ),
        name="project-stakeholders-list",
    ),
    path(
        "<int:project_pk>/stakeholders/<int:pk>/",
        StakeholderViewSet.as_view(
            {"get": "retrieve", "put": "update", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-stakeholders-detail",
    ),
    path("", include(router.urls)),
]
