from datetime import date

from django.http import Http404
from django.test.client import RequestFactory

from mock import patch
from nose.tools import eq_, ok_

from affiliates.base.tests import aware_datetime, TestCase
from affiliates.links import views
from affiliates.links.tests import LinkFactory
from affiliates.users.tests import UserFactory


class LinkDetailViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_queryset(self):
        """
        Available links should be limited to those owned by the current
        user.
        """
        request = self.factory.get('/')
        request.user = UserFactory.create()

        link1, link2 = LinkFactory.create_batch(2, user=request.user)
        unowned_link = LinkFactory.create()

        view = views.LinkDetailView()
        view.request = request
        qs = view.get_queryset()

        ok_(link1 in qs)
        ok_(link2 in qs)
        ok_(unowned_link not in qs)


class LinkReferralViewTest(TestCase):
    def setUp(self):
        self.view = views.LinkReferralView.as_view()
        self.factory = RequestFactory()

    def test_add_click(self):
        request = self.factory.get('/')
        link = LinkFactory.create()

        with patch('affiliates.links.views.add_click') as add_click:
            with patch('affiliates.links.views.timezone') as timezone:
                timezone.now.return_value = aware_datetime(2014, 4, 7)

                self.view(request, pk=link.pk)
                add_click.delay.assert_called_with(link.id, date(2014, 4, 7))


class LegacyLinkReferralViewTests(TestCase):
    def test_get_object_404(self):
        view = views.LegacyLinkReferralView()
        view.kwargs = {'user_id': '999999999999', 'banner_img_id': '74'}

        with self.assertRaises(Http404):
            view.get_object()

    def test_get_object(self):
        link = LinkFactory.create(legacy_banner_image_id=7)
        view = views.LegacyLinkReferralView()
        view.kwargs = {'user_id': unicode(link.user.id), 'banner_img_id': '7'}

        eq_(view.get_object(), link)
