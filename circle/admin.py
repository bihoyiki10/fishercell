from django.contrib import admin

from .models import Choice, Participant


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
	list_display = ['name', 'choice_status']
	search_fields = ['name']
	ordering = ['name']

	@admin.display(description='Choice made')
	def choice_status(self, participant):
		return hasattr(participant, 'choice_made')


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
	list_display = ['chooser', 'selected', 'created_at']
	list_select_related = ['chooser', 'selected']
	search_fields = ['chooser__name', 'selected__name']
