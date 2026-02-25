# Ivy Opportunity Network

Real-Time Ivy League Opportunity Intelligence and Student Competency Network built with Django.

## Implemented Modules

1. Real-Time Opportunity Extraction Module
- Ivy League scraper manager in `apps/scraper/scrapers.py`
- Scheduled task entry points in `apps/scraper/tasks.py`
- University seed script in `scripts/init_db.py`

2. AI-Based Domain Classification Module
- Opportunity classifier in `apps/classification/classifier.py`
- Manual classification endpoints in `apps/classification/views.py`
- Routes in `apps/classification/urls.py`

3. Student Profile and Personalization Module
- Extended user model and achievements in `apps/accounts/models.py`
- Personalized recommendations in `apps/opportunities/views.py`

4. Auto-Application Support (MVP)
- Application and tracking models in `apps/opportunities/models.py`
- User opportunity workflow (save/applied/accepted) in opportunities APIs/views

5. Academic Community Platform
- Posts, comments, groups in `apps/community/models.py`
- Web pages and APIs in `apps/community/views.py` and `apps/community/api.py`

6. InCoScore Ranking Engine
- Scoring logic in `apps/ranking/incoscore.py`
- Leaderboard pages and APIs in `apps/ranking/views.py` and `apps/ranking/api.py`

## Tech Stack

- Backend: Django + Django REST Framework
- Real-time support: Channels (in-memory backend by default)
- Scraping: Requests + BeautifulSoup (+ Selenium support for dynamic pages)
- AI/NLP: Scikit-learn + optional Transformers/NLTK pipeline
- Database: SQLite (default)

## Quick Start

1. Create and activate virtual environment.
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Run migrations:
```bash
python manage.py migrate
```
4. Seed Ivy universities + admin:
```bash
python scripts/init_db.py
```
5. Start server:
```bash
python manage.py runserver
```

## Default URLs

- Home: `/`
- Opportunities: `/opportunities/`
- Dashboard: `/opportunities/dashboard/`
- Community: `/community/`
- Ranking: `/ranking/`
- Classification utility: `/classification/pending/`
- API root: `/api/`

## Notes

- Classifier supports a robust fallback mode when transformer models are not available.
- Celery tasks are configured to run eagerly in development (`CELERY_TASK_ALWAYS_EAGER = True`).
- Email output defaults to console backend for local testing.
