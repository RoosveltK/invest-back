"""
pytest fixtures shared across all test modules.
Provides API clients pre-authenticated for each stakeholder role.
"""
import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from projects.models import Project, Stakeholder
from tests.factories import ProjectFactory, StakeholderFactory, UserFactory


def get_jwt_client(user):
    """Return a DRF APIClient authenticated with a JWT for the given user."""
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def owner_user(db):
    return UserFactory()


@pytest.fixture
def collaborator_user(db):
    return UserFactory()


@pytest.fixture
def observer_user(db):
    return UserFactory()


@pytest.fixture
def shareholder_user(db):
    return UserFactory()


@pytest.fixture
def other_user(db):
    """A user who has no stake in the project."""
    return UserFactory()


@pytest.fixture
def project(db, owner_user):
    project = ProjectFactory(owner=owner_user)
    # Add owner stakeholder
    StakeholderFactory(
        user=owner_user,
        project=project,
        role=Stakeholder.Role.OWNER,
        email=owner_user.email,
        first_name=owner_user.first_name,
        last_name=owner_user.last_name,
    )
    return project


@pytest.fixture
def setup_roles(db, project, collaborator_user, observer_user, shareholder_user):
    """Create stakeholders for each role on the test project."""
    StakeholderFactory(
        user=collaborator_user,
        project=project,
        role=Stakeholder.Role.COLLABORATOR,
        email=collaborator_user.email,
        first_name=collaborator_user.first_name,
        last_name=collaborator_user.last_name,
    )
    StakeholderFactory(
        user=observer_user,
        project=project,
        role=Stakeholder.Role.OBSERVER,
        email=observer_user.email,
        first_name=observer_user.first_name,
        last_name=observer_user.last_name,
    )
    StakeholderFactory(
        user=shareholder_user,
        project=project,
        role=Stakeholder.Role.SHAREHOLDER,
        email=shareholder_user.email,
        first_name=shareholder_user.first_name,
        last_name=shareholder_user.last_name,
    )
    return project


@pytest.fixture
def owner_client(owner_user):
    return get_jwt_client(owner_user)


@pytest.fixture
def collaborator_client(collaborator_user):
    return get_jwt_client(collaborator_user)


@pytest.fixture
def observer_client(observer_user):
    return get_jwt_client(observer_user)


@pytest.fixture
def shareholder_client(shareholder_user):
    return get_jwt_client(shareholder_user)


@pytest.fixture
def other_client(other_user):
    return get_jwt_client(other_user)
