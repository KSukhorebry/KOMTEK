from datetime import timedelta

from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from terminology.models import RefBook, RefBookElement, RefBookVersion


class RefBookApiTests(APITestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.refbook = RefBook.objects.create(code='RB1', name='Справочник один')
        self.past_version = RefBookVersion.objects.create(
            refbook=self.refbook,
            version='1.0',
            start_date=self.today - timedelta(days=30),
        )
        self.current_version = RefBookVersion.objects.create(
            refbook=self.refbook,
            version='2.0',
            start_date=self.today - timedelta(days=1),
        )
        self.future_version = RefBookVersion.objects.create(
            refbook=self.refbook,
            version='3.0',
            start_date=self.today + timedelta(days=30),
        )
        RefBookElement.objects.create(
            refbook_version=self.past_version, code='X1', value='Старое значение'
        )
        RefBookElement.objects.create(
            refbook_version=self.current_version, code='X1', value='Текущее значение'
        )
        self.other_refbook = RefBook.objects.create(code='RB2', name='Без версий')

    def test_lists_all_refbooks(self):
        response = self.client.get(reverse('refbook-list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['refbooks']), 2)
        self.assertEqual(response.data['refbooks'][0]['id'], self.refbook.pk)

    def test_filters_refbooks_by_date_without_duplicates(self):
        requested_date = self.today.isoformat()
        response = self.client.get(reverse('refbook-list'), {'date': requested_date})
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.data['refbooks']], [self.refbook.pk])

    def test_excludes_refbooks_without_a_version_on_requested_date(self):
        before_first_version = self.today - timedelta(days=40)
        response = self.client.get(
            reverse('refbook-list'), {'date': before_first_version.isoformat()}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['refbooks'], [])

    def test_rejects_invalid_date(self):
        response = self.client.get(reverse('refbook-list'), {'date': '20-10-2026'})
        self.assertEqual(response.status_code, 400)

    def test_gets_requested_version_elements(self):
        response = self.client.get(
            reverse('refbook-elements', args=[self.refbook.pk]), {'version': '1.0'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['elements'], [{'code': 'X1', 'value': 'Старое значение'}])

    def test_gets_current_version_and_ignores_future_version(self):
        response = self.client.get(reverse('refbook-elements', args=[self.refbook.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['elements'], [{'code': 'X1', 'value': 'Текущее значение'}])

    def test_unknown_refbook_returns_404(self):
        response = self.client.get(reverse('refbook-elements', args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_unknown_or_foreign_version_returns_404(self):
        for version in ('missing', 'foreign'):
            with self.subTest(version=version):
                if version == 'foreign':
                    foreign_book = RefBook.objects.create(code='RB3', name='Другой')
                    RefBookVersion.objects.create(
                        refbook=foreign_book, version='foreign', start_date=self.today
                    )
                response = self.client.get(
                    reverse('refbook-elements', args=[self.refbook.pk]),
                    {'version': version},
                )
                self.assertEqual(response.status_code, 404)

    def test_no_current_version_returns_404_and_empty_version_returns_empty_list(self):
        response = self.client.get(reverse('refbook-elements', args=[self.other_refbook.pk]))
        self.assertEqual(response.status_code, 404)
        empty_version = RefBookVersion.objects.create(
            refbook=self.other_refbook, version='empty', start_date=self.today
        )
        response = self.client.get(
            reverse('refbook-elements', args=[self.other_refbook.pk]),
            {'version': empty_version.version},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['elements'], [])

    def test_check_element_requires_code_and_value(self):
        response = self.client.get(
            reverse('refbook-check-element', args=[self.refbook.pk]), {'code': 'X1'}
        )
        self.assertEqual(response.status_code, 400)

    def test_check_element_matches_code_and_value_together(self):
        url = reverse('refbook-check-element', args=[self.refbook.pk])
        valid = self.client.get(url, {'code': 'X1', 'value': 'Текущее значение'})
        wrong_value = self.client.get(url, {'code': 'X1', 'value': 'Другое'})
        unknown_code = self.client.get(url, {'code': 'missing', 'value': 'Текущее значение'})
        self.assertEqual(valid.data, {'is_valid': True})
        self.assertEqual(wrong_value.data, {'is_valid': False})
        self.assertEqual(unknown_code.data, {'is_valid': False})

    def test_check_element_isolated_by_version_and_refbook(self):
        url = reverse('refbook-check-element', args=[self.refbook.pk])
        old_version = self.client.get(
            url,
            {'code': 'X1', 'value': 'Старое значение', 'version': '1.0'},
        )
        old_mismatch = self.client.get(
            url,
            {'code': 'X1', 'value': 'Старое значение', 'version': '2.0'},
        )
        self.assertEqual(old_version.data, {'is_valid': True})
        self.assertEqual(old_mismatch.data, {'is_valid': False})

    def test_check_unknown_refbook_or_version_returns_404(self):
        missing_book = self.client.get(
            reverse('refbook-check-element', args=[9999]), {'code': 'X1', 'value': 'x'}
        )
        missing_version = self.client.get(
            reverse('refbook-check-element', args=[self.refbook.pk]),
            {'code': 'X1', 'value': 'x', 'version': 'absent'},
        )
        no_current = self.client.get(
            reverse('refbook-check-element', args=[self.other_refbook.pk]),
            {'code': 'X1', 'value': 'x'},
        )
        self.assertEqual(missing_book.status_code, 404)
        self.assertEqual(missing_version.status_code, 404)
        self.assertEqual(no_current.status_code, 404)


class ModelConstraintTests(APITestCase):
    def setUp(self):
        self.today = timezone.localdate()
        self.refbook = RefBook.objects.create(code='UNIQUE', name='Ограничения')
        self.version = RefBookVersion.objects.create(
            refbook=self.refbook, version='1', start_date=self.today
        )

    def assertIntegrityError(self, operation):
        with self.assertRaises(IntegrityError), transaction.atomic():
            operation()

    def test_refbook_code_is_unique(self):
        self.assertIntegrityError(
            lambda: RefBook.objects.create(code='UNIQUE', name='Дубль')
        )

    def test_refbook_version_pair_is_unique(self):
        self.assertIntegrityError(
            lambda: RefBookVersion.objects.create(
                refbook=self.refbook, version='1', start_date=self.today + timedelta(days=1)
            )
        )

    def test_refbook_start_date_pair_is_unique(self):
        self.assertIntegrityError(
            lambda: RefBookVersion.objects.create(
                refbook=self.refbook, version='2', start_date=self.today
            )
        )

    def test_element_code_is_unique_per_version_but_allowed_in_another(self):
        RefBookElement.objects.create(refbook_version=self.version, code='A', value='one')
        self.assertIntegrityError(
            lambda: RefBookElement.objects.create(
                refbook_version=self.version, code='A', value='two'
            )
        )
        another_version = RefBookVersion.objects.create(
            refbook=self.refbook, version='2', start_date=self.today + timedelta(days=1)
        )
        RefBookElement.objects.create(refbook_version=another_version, code='A', value='two')