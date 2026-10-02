from django.db import models


class Participant(models.Model):
	name = models.CharField(max_length=80, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Choice(models.Model):
	chooser = models.OneToOneField(
		Participant, on_delete=models.CASCADE, related_name='choice_made'
	)
	selected = models.OneToOneField(
		Participant, on_delete=models.CASCADE, related_name='chosen_by'
	)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.chooser} chose {self.selected}'
