# Bus Reservation System

## Project overview
A Django-based web app to search buses, pick seats, book tickets, and pay online. It includes a focused admin portal for managing buses, bookings, and generating reports.

## Features implemented
- Authentication: Email-based login (custom user model), admin/staff support
- Search & booking: Filter active buses, schedules, seat selection, PNR generation
- Payments: Razorpay integration (order/payment/signature) with status tracking
- Reviews: Per-booking reviews by users
- Admin portal: At `bus-admin/` with login, dashboard, manage buses/bookings, reports

## Tech stack
- Backend: Django 5.x, SQLite (default)
- Frontend: Bootstrap, jQuery, Select2, Font Awesome; SCSS sources included
- Django apps: `core` (public), `bus_management` (admin portal)
- Utilities: `django-bootstrap5`, `django-widget-tweaks`, `razorpay`
## Setup instructions (how to run)

Prerequisites
- Python 3.10+
- Node.js and npm (optional; for local frontend assets)

Windows PowerShell steps
1) Enter the project directory
```powershell
cd bus_reservation
```

2) Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3) Install Python dependencies
```powershell
pip install -r requirements.txt
```

4) Apply database migrations (manage.py is in a nested folder)
```powershell
cd .\bus_reservation\bus_reservation
python manage.py migrate
```

5) (Optional) Create a superuser
```powershell
python manage.py createsuperuser
```

6) Run the development server
```powershell
python manage.py runserver
```
Open http://127.0.0.1:8000/

Frontend packages (optional)
- PowerShell may block npm.ps1. Use one of:
```powershell
"C:\\Program Files\\nodejs\\npm.cmd" install jquery select2 xregexp bootstrap @fortawesome/fontawesome-free
# or
cmd /c "npm install jquery select2 xregexp bootstrap @fortawesome/fontawesome-free"
```
6) Install frontend packages
- PowerShell often blocks npm.ps1. Use one of:
```powershell
# Use npm.cmd directly
"C:\\Program Files\\nodejs\\npm.cmd" install jquery select2 xregexp bootstrap @fortawesome/fontawesome-free

# Or via cmd
cmd /c "npm install jquery select2 xregexp bootstrap @fortawesome/fontawesome-free"
```

7) Run the dev server
```powershell
python ..\..\.venv\Scripts\python.exe manage.py runserver
```
Then open http://127.0.0.1:8000/

## Configuration (.env)
Copy `.env.example` to `.env` and fill values, then wire them in `settings.py` (recommended for production):
- DJANGO_SECRET_KEY
- DJANGO_DEBUG
- RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
- EMAIL_HOST_USER, EMAIL_HOST_PASSWORD

Note: The sample settings currently hardcode email and Razorpay keys; move to environment variables before publishing.

## Static files
For production:
```powershell
python ..\..\.venv\Scripts\python.exe manage.py collectstatic
```

## Troubleshooting
- PowerShell npm error: “npm.ps1 cannot be loaded”
  - Use `"C:\\Program Files\\nodejs\\npm.cmd"` or `cmd /c "npm ..."`
  - Or: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

- ImportError `bootstrap5` / `django_bootstrap5`:
  - Ensure `INSTALLED_APPS` has `django_bootstrap5` and `pip install django-bootstrap5` is done.

- Razorpay `pkg_resources` warning:
  - Setuptools < 81 is pinned in requirements; keep it or upgrade Razorpay when available.

## License
Choose a license before publishing (e.g., MIT). Add a LICENSE file to the repo.
