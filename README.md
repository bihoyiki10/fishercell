# Fishercell: Choice Circle

A small Django app where each participant enters their name and the system randomly assigns one available person. Each participant can draw once, and each person can be selected once. The saved result is shown with a heart reveal for two minutes and can be looked up later by entering the participant's name again.

## Participants

The initial names are Gilbert, Benitha, Paradi, Loic, Mugisha, and Dosite. They are seeded by the first migration. Add or remove participants and review choices in Django Admin at `/admin/` after creating a staff account.

## Run locally

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/` for the participant page and `http://127.0.0.1:8000/admin/` for administration. Admin changes require a staff account. The development server is intended for local use, not production deployment.

## Test

```powershell
python manage.py test
```

## Deploy

Push this repository to GitHub, then create a Render Blueprint from the repository and select `render.yaml`. Set `ADMIN_PASSWORD` as a secret environment variable in Render before deploying. The build creates the `admin` superuser if it does not already exist; it never resets an existing account's password.
