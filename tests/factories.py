"""
Factory Boy factories for test fixtures.
All factories use lazy sequences and Faker for realistic test data.
"""
import factory
from factory.django import DjangoModelFactory

from accounts.models import CustomUser
from projects.models import Project, Stakeholder
from transactions.models import RecurringTransaction, Transaction


class UserFactory(DjangoModelFactory):
    class Meta:
        model = CustomUser

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    phone_number = factory.Faker("phone_number")
    is_email_verified = True
    is_active = True
    password = factory.PostGenerationMethodCall("set_password", "testpassword123")


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    name = factory.Sequence(lambda n: f"Project {n}")
    project_type = Project.ProjectType.INVESTMENT
    start_date = factory.Faker("date_this_decade")
    initial_budget = factory.Faker("pydecimal", left_digits=6, right_digits=2, positive=True)
    description = factory.Faker("paragraph")
    status = Project.Status.ONGOING
    owner = factory.SubFactory(UserFactory)


class StakeholderFactory(DjangoModelFactory):
    class Meta:
        model = Stakeholder

    user = factory.SubFactory(UserFactory)
    project = factory.SubFactory(ProjectFactory)
    first_name = factory.LazyAttribute(lambda o: o.user.first_name if o.user else "Ghost")
    last_name = factory.LazyAttribute(lambda o: o.user.last_name if o.user else "User")
    email = factory.LazyAttribute(
        lambda o: o.user.email if o.user else f"ghost_{factory.Sequence(lambda n: n)()}@example.com"
    )
    role = Stakeholder.Role.OBSERVER


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    project = factory.SubFactory(ProjectFactory)
    transaction_type = Transaction.TransactionType.EXPENSE
    amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    category = factory.Faker("word")
    description = factory.Faker("sentence")
    author = factory.SubFactory(UserFactory)


class RecurringTransactionFactory(DjangoModelFactory):
    class Meta:
        model = RecurringTransaction

    project = factory.SubFactory(ProjectFactory)
    transaction_type = RecurringTransaction.TransactionType.EXPENSE
    amount = factory.Faker("pydecimal", left_digits=4, right_digits=2, positive=True)
    frequency = RecurringTransaction.Frequency.MONTHLY
    start_date = factory.Faker("date_this_year")
    is_active = True
