import factory


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'auth.User'
