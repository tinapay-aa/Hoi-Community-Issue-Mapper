# Hoi! - Community Complaint Mapper

Hoi! is a web app that lets residents report community problems such as broken roads or piling trash by pinning them on a map. Issues are grouped by community, tracked through a status workflow, and can only be closed with photo proof, so everyone can see what has been reported and what has actually been fixed.

## Features

- **Interactive issue map**: all issues are shown as color-coded pins (by status) on an OpenStreetMap map, with marker clustering when zoomed out.
- **Click-to-report**: click anywhere on the map to drop a pin and report an issue. The address is filled in automatically through reverse geocoding.
- **Full issue CRUD**: create, view, edit, and delete issues with a title, description, category, community, priority, and evidence photos.
- **Resolution proof**: marking an issue as Resolved requires an attached photo.
- **Status history**: every status change is logged with who made it, when, and optional remarks.
- **Comments**: logged-in users can add, edit, and delete comments on issues, directly from the map panel (JSON endpoints).
- **Communities**: create, edit, archive, and delete communities, each with its own map location, description, and issue/member counts.
- **Roles and permissions**: Member, Moderator, and Admin roles per community. Reporters can edit their own issues, while managers can update any status and priority.
- **Search and filters**: search issues by title, description, or address, filter by community, or show only the issues you reported.
- **Authentication**: sign up and log in with username or email (with email verification), or continue with Google or GitHub.
- **Guest access**: visitors can browse the map, issues, and communities without logging in, but cannot make changes.
- **Profile settings**: change username, upload or remove an avatar, and manage email, password, and connected social accounts.
- **Progressive Web App**: web manifest, service worker, and offline page.
- **Responsive UI**: sidebar becomes a slide-out drawer on mobile.
- **Admin panel**: manage all data through the Django admin.

## Data Models

`Category`, `Community`, `CommunityMembership`, `Location`, `Issue`, `IssueImage`, `IssueUpdate`, `IssueComment`, `Profile`

## Tech Stack

**Backend**
- Python
- Django 6.1
- django-allauth (email/password, Google and GitHub login)
- SQLite
- Pillow (image uploads)
- python-dotenv (environment variables)

**Frontend**
- Django templates, HTML, CSS, vanilla JavaScript
- Bootstrap 5.3 and Bootstrap Icons
- Google Fonts (Bricolage Grotesque, Public Sans)

**Maps and external services**
- Leaflet.js 1.9 with Leaflet.markercluster
- OpenStreetMap tiles
- Nominatim API (reverse geocoding and place search)
- Google and GitHub OAuth

## Getting Started

```bash
cd HOI
pip install django django-allauth python-dotenv pillow requests pyjwt cryptography
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Create `HOI/.env` for social login (optional):

```
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
```

Then open http://127.0.0.1:8000/. Verification emails are printed in the terminal during development.


## Developers

- ### [Russel Aaron A. Sarastal](https://github.com/tinapay-aa) <br>
- ### [Christian Dave C. Denzon](https://github.com/Ch8967) <br>
- ### [Mark Kevin B. Sanchez](https://github.com/vioxvanitas) <br>
- ### [Ralph Jeffrey A. Cerdeña](https://github.com/Lucky70fu) <br>