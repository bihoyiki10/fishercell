import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
	"""Create the initial admin from Render environment variables."""

	help = 'Create an admin account when ADMIN_PASSWORD is configured.'

	def handle(self, *args, **options):
		password = os.environ.get('ADMIN_PASSWORD')
		if not password:
			self.stdout.write('ADMIN_PASSWORD is unset; skipping admin bootstrap.')
			return

		username = os.environ.get('ADMIN_USERNAME', 'admin')
		user_model = get_user_model()
		user, created = user_model.objects.get_or_create(
			username=username,
			defaults={'is_staff': True, 'is_superuser': True, 'is_active': True},
		)
		if created:
			user.set_password(password)
			user.save(update_fields=['password'])
		else:
			changed = []
			for field in ('is_staff', 'is_superuser', 'is_active'):
				if not getattr(user, field):
					setattr(user, field, True)
					changed.append(field)
			if changed:
				user.save(update_fields=changed)

		self.stdout.write(f'Admin account {username!r} is ready.')