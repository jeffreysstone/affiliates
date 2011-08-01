import hashlib
import random

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import render_to_string

from tower import ugettext as _
from tower import ugettext_lazy as _lazy

from affiliates.models import ModelBase, LocaleField
from countries import COUNTRIES


class UserProfile(ModelBase):
    """
    Stores information about a user account. Created post-activation.
    Accessible via user.get_profile().
    """

    user = models.OneToOneField(User, primary_key=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, verbose_name=_lazy(u'Full Name'))
    email = models.EmailField(unique=True, verbose_name=_lazy(u'Email'))

    address_1 = models.CharField(max_length=255, blank=True, null=True,
                                 verbose_name=_lazy(u'Address Line 1'))
    address_2 = models.CharField(max_length=255, blank=True, null=True,
                                 verbose_name=_lazy(u'Address Line 2'))
    city = models.CharField(max_length=255, blank=True, null=True,
                                 verbose_name=_lazy(u'City'))
    state = models.CharField(max_length=255, blank=True, null=True,
                                 verbose_name=_lazy(u'State or Province'))

    locale = LocaleField(verbose_name=_lazy(u'Locale'))
    country = models.CharField(max_length=2, choices=COUNTRIES,
                               verbose_name=_lazy(u'Country'))

    accept_email = models.BooleanField(verbose_name=_lazy(u'Receive emails'))

    def __unicode__(self):
        return unicode(self.email)


class RegisterManager(models.Manager):
    """
    Custom manager for creating registration profiles and activating them.

    Users are sent an email upon creation that contains a link with an
    activation code. This code will create their account and direct the user
    to fill out their profile information.
    """

    def create_profile(self, name, email, password):
        """
        Create a registration profile and return it. Also sends an activation
        email to the given email address.

        Activation keys are a hash generated from the user's email and a
        random salt.
        """
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        activation_key = hashlib.sha1(salt + email).hexdigest()

        profile = RegisterProfile(name=name, email=email,
                                  activation_key=activation_key)
        profile.set_password(password)
        profile.save()

        self._send_email('users/email/activation.ltxt',
                         _('Please activate your account'), profile)

        return profile

    def activate_profile(self, activation_key):
        pass

    def _send_email(self, template, subject, profile, **kwargs):
        """Sends an activation email to the user"""
        current_site = Site.objects.get_current()
        url = reverse('users.activate',
                     kwargs={'activation_key': profile.activation_key})
        email_kwargs = {'domain': current_site.domain,
                        'activate_url': url}
        email_kwargs.update(kwargs)
        message = render_to_string(template, email_kwargs)
        mail.send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
                       [profile.email])


class RegisterProfile(ModelBase):
    """Stores activation information for a user."""
    activation_key = models.CharField(max_length=40,
                                      verbose_name=_lazy(u'Activation Key'))
    name = models.CharField(max_length=255, verbose_name=_lazy(u'Full Name'))
    email = models.EmailField(unique=True, verbose_name=_lazy(u'Email'))
    password = models.CharField(max_length=255,
                                verbose_name=_lazy(u'Password'))
    user = models.OneToOneField(User, null=True)

    objects = RegisterManager()

    def set_password(self, raw_password):
        """
        Sets the profile's password to a properly hashed password by passing
        it through a User object.
        """
        user = User()
        user.set_password(raw_password)
        self.password = user.password

    def __unicode__(self):
        return u'Registration information for %s' % self.name