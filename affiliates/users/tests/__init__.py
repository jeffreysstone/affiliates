from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save

from factory import DjangoModelFactory, RelatedFactory, Sequence, SubFactory
from factory.django import mute_signals

from affiliates.users import models


class UserProfileFactory(DjangoModelFactory):
    FACTORY_FOR = models.UserProfile

    display_name = Sequence(lambda n: 'test{0}'.format(n))
    website = 'http://www.mozilla.org'
    bio = Sequence(lambda n: 'bio{0}'.format(n))


@mute_signals(post_save)
class UserFactory(DjangoModelFactory):
    FACTORY_FOR = User

    username = Sequence(lambda n: 'test%s' % n)
    email = Sequence(lambda n: 'test%s@example.com' % n)
    userprofile = RelatedFactory(UserProfileFactory, 'user')


class ContentTypeFactory(DjangoModelFactory):
    FACTORY_FOR = ContentType

    name = Sequence(lambda n: 'test%s' % n)
    app_label = Sequence(lambda n: 'test%s' % n)
    model = Sequence(lambda n: 'test%s' % n)


class PermissionFactory(DjangoModelFactory):
    FACTORY_FOR = Permission

    name = Sequence(lambda n: 'test%s' % n)
    codename = Sequence(lambda n: 'test%s' % n)
    content_type = SubFactory(ContentTypeFactory)
