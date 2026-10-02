from datetime import timedelta
import random

from django.db import IntegrityError, transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .models import Choice, Participant


REVEAL_SECONDS = 120
SESSION_CHOOSER_KEY = 'choice_circle_chooser_id'


def _participant_for_name(participants, name):
	name = name.strip().casefold()
	return next((person for person in participants if person.name.casefold() == name), None)


def _participant_for_id(participants, participant_id):
	return next((person for person in participants if str(person.pk) == str(participant_id)), None)


def home(request):
	participants = list(Participant.objects.all())
	locked_chooser = _participant_for_id(
		participants, request.session.get(SESSION_CHOOSER_KEY)
	)
	chooser = locked_chooser
	saved_choice = None
	reveal_seconds = 0
	notice = ''
	name_input = ''

	if request.method == 'POST':
		name_input = request.POST.get('chooser', '').strip()
		submitted_chooser = _participant_for_name(participants, name_input)

		if locked_chooser and submitted_chooser != locked_chooser:
			chooser = locked_chooser
			name_input = chooser.name
			saved_choice = Choice.objects.filter(chooser=chooser).select_related('selected').first()
			notice = f'This browser already made a choice as {chooser.name}. You cannot switch names.'
		elif submitted_chooser is None:
			chooser = None
			notice = 'Enter a participant name from the circle.'
		else:
			chooser = submitted_chooser
			created_choice = False
			saved_choice = Choice.objects.filter(chooser=chooser).select_related('selected').first()
			if saved_choice:
				notice = f'{chooser.name}, you already made your choice. Your original choice is shown again.'
			else:
				try:
					with transaction.atomic():
						selected_ids = set(Choice.objects.values_list('selected_id', flat=True))
						available = [
							person for person in participants
							if person.pk not in selected_ids and person.pk != chooser.pk
						]
						if available:
							selected = random.choice(available)
							saved_choice = Choice.objects.create(chooser=chooser, selected=selected)
							saved_choice = Choice.objects.select_related('selected').get(pk=saved_choice.pk)
							created_choice = True
					if saved_choice:
						notice = 'Your choice is saved. ♥'
					else:
						notice = 'A new choice cannot be made right now.'
				except IntegrityError:
					saved_choice = Choice.objects.filter(chooser=chooser).select_related('selected').first()
					notice = 'Your saved choice is shown below.' if saved_choice else 'The circle just changed. Please enter your name again.'

			if saved_choice:
				request.session[SESSION_CHOOSER_KEY] = chooser.pk
				request.session[f'reveal_until_{chooser.pk}'] = (timezone.now() + timedelta(seconds=REVEAL_SECONDS)).timestamp()
				if submitted_chooser == locked_chooser or locked_chooser is None:
					spin = '&spin=1' if created_choice else ''
					return redirect(f'/?chooser_id={chooser.pk}&fresh=1{spin}')

	if request.method == 'GET':
		if locked_chooser:
			chooser = locked_chooser
			requested_name = request.GET.get('chooser', '').strip()
			requested_id = request.GET.get('chooser_id')
			requested_chooser = _participant_for_name(participants, requested_name) if requested_name else _participant_for_id(participants, requested_id)
			if requested_chooser and requested_chooser != locked_chooser:
				notice = f'This browser already made a choice as {locked_chooser.name}. You cannot switch names.'
			name_input = chooser.name
		elif request.GET.get('lookup') == '1':
			name_input = request.GET.get('chooser', '').strip()
			chooser = _participant_for_name(participants, name_input)
			if chooser is None:
				notice = 'Enter a participant name from the circle to look up a choice.'
		else:
			chooser = _participant_for_id(participants, request.GET.get('chooser_id'))

	if chooser and saved_choice is None:
		saved_choice = Choice.objects.filter(chooser=chooser).select_related('selected').first()
	if chooser and saved_choice:
		request.session.setdefault(SESSION_CHOOSER_KEY, chooser.pk)

	if chooser and saved_choice:
		if request.GET.get('fresh') == '1':
			reveal_until = request.session.get(f'reveal_until_{chooser.pk}', 0)
		elif request.GET.get('lookup') == '1':
			reveal_until = (timezone.now() + timedelta(seconds=REVEAL_SECONDS)).timestamp()
			request.session[f'reveal_until_{chooser.pk}'] = reveal_until
		else:
			reveal_until = request.session.get(f'reveal_until_{chooser.pk}', 0)
		reveal_seconds = max(0, int(reveal_until - timezone.now().timestamp()))
		if not notice:
			notice = f'{chooser.name}, you already made your choice. Your original choice is shown again.'

	return render(request, 'circle/home.html', {
		'participants': participants,
		'chooser': chooser,
		'name_input': name_input,
		'saved_choice': saved_choice,
		'notice': notice,
		'reveal_seconds': reveal_seconds,
		'should_spin': request.GET.get('spin') == '1',
	})
