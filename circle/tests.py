import os
from django.test import Client, TestCase
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.core.management import call_command
from unittest.mock import patch

from .models import Choice, Participant


class ChoiceCircleTests(TestCase):
	def setUp(self):
		self.people = {
			name: Participant.objects.get_or_create(name=name)[0]
			for name in ['Gilbert', 'Benitha', 'Paradi', 'Loic', 'Mugisha', 'Dosite']
		}
		self.url = reverse('circle:home')

	def test_roster_is_displayed(self):
		response = self.client.get(self.url)
		self.assertEqual(response.status_code, 200)
		for name in self.people:
			self.assertContains(response, name)

	@patch('circle.views.random.choice')
	def test_name_only_draw_is_random_and_uses_unique_people(self, draw):
		draw.side_effect = lambda options: options[0]
		response = self.client.post(self.url, {'chooser': '  Gilbert  '})
		self.assertRedirects(response, f'{self.url}?chooser_id={self.people["Gilbert"].pk}&fresh=1&spin=1')
		response = self.client.get(response.url)
		self.assertContains(response, 'class="wheel-stage"')
		self.assertContains(response, 'is-spinning')
		self.assertContains(response, 'Benitha')
		first_choice = Choice.objects.get(chooser=self.people['Gilbert'])
		self.assertEqual(first_choice.selected, self.people['Benitha'])
		self.assertNotEqual(first_choice.selected, first_choice.chooser)

		response = self.client.post(self.url, {'chooser': 'Gilbert'}, follow=True)
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Gilbert, you already made your choice. Your original choice is shown again.')
		self.assertContains(response, 'Benitha')
		self.assertNotContains(response, 'class="wheel-stage"')
		self.assertEqual(Choice.objects.get(chooser=self.people['Gilbert']).selected, self.people['Benitha'])
		self.assertEqual(draw.call_count, 1)

		Client().post(self.url, {'chooser': 'Loic'})
		second_choice = Choice.objects.get(chooser=self.people['Loic'])
		self.assertNotEqual(second_choice.selected, self.people['Benitha'])
		self.assertNotEqual(second_choice.selected, self.people['Loic'])
		self.assertEqual(Choice.objects.count(), 2)

	@patch('circle.views.random.choice')
	def test_session_cannot_switch_to_another_name_after_choice(self, draw):
		draw.side_effect = lambda options: options[0]
		self.client.post(self.url, {'chooser': 'Gilbert'})
		first_choice = Choice.objects.get(chooser=self.people['Gilbert'])

		response = self.client.post(self.url, {'chooser': 'Benitha'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'This browser already made a choice as Gilbert. You cannot switch names.')
		self.assertContains(response, first_choice.selected.name)
		self.assertContains(response, 'This browser is locked to this name.')
		self.assertNotContains(response, 'id="chooser"')
		self.assertFalse(Choice.objects.filter(chooser=self.people['Benitha']).exists())
		self.assertEqual(draw.call_count, 1)

	def test_client_has_one_name_field_and_no_target_dropdown(self):
		response = self.client.get(self.url)
		self.assertContains(response, 'Enter your name')
		self.assertContains(response, 'name="chooser"')
		self.assertNotContains(response, 'Who do you choose?')
		self.assertNotContains(response, 'name="selected"')
		self.assertNotContains(response, 'Available')
		self.assertNotContains(response, 'Chosen')

	def test_client_roster_does_not_reveal_assignment_statuses(self):
		Choice.objects.create(chooser=self.people['Gilbert'], selected=self.people['Dosite'])
		response = self.client.get(self.url)
		self.assertContains(response, 'Gilbert')
		self.assertContains(response, 'Dosite')
		self.assertNotContains(response, 'Available')
		self.assertNotContains(response, 'Chosen')
		self.assertNotContains(response, 'claimed')

	def test_invalid_name_does_not_create_a_choice(self):
		response = self.client.post(self.url, {'chooser': 'Not in the circle'})
		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Enter a participant name from the circle.')
		self.assertEqual(Choice.objects.count(), 0)

	def test_database_rejects_selecting_the_same_person_twice(self):
		Choice.objects.create(chooser=self.people['Gilbert'], selected=self.people['Dosite'])

		with self.assertRaises(IntegrityError):
			with transaction.atomic():
				Choice.objects.create(chooser=self.people['Benitha'], selected=self.people['Dosite'])

		self.assertEqual(Choice.objects.filter(selected=self.people['Dosite']).count(), 1)

	@patch.dict(os.environ, {'ADMIN_PASSWORD': 'test-admin-password', 'ADMIN_USERNAME': 'admin'})
	def test_admin_bootstrap_creates_admin_without_resetting_existing_password(self):
		from django.contrib.auth import get_user_model

		call_command('bootstrap_admin', verbosity=0)
		admin_user = get_user_model().objects.get(username='admin')
		self.assertTrue(admin_user.is_staff)
		self.assertTrue(admin_user.is_superuser)
		self.assertTrue(admin_user.check_password('test-admin-password'))

		admin_user.set_password('manually-changed-password')
		admin_user.save(update_fields=['password'])
		call_command('bootstrap_admin', verbosity=0)
		admin_user.refresh_from_db()
		self.assertTrue(admin_user.check_password('manually-changed-password'))

	def test_saved_choice_can_be_looked_up_again(self):
		Choice.objects.create(chooser=self.people['Gilbert'], selected=self.people['Dosite'])
		response = self.client.get(self.url, {'chooser': 'Gilbert', 'lookup': '1'})
		self.assertContains(response, 'Dosite')
		self.assertContains(response, 'is-revealing')
