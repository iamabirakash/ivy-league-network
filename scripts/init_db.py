#!/usr/bin/env python
import os
import sys
import django
from django.contrib.auth import get_user_model

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.opportunities.models import University


def create_universities():
    """Create Ivy League universities"""
    universities = [
        {
            'name': 'Harvard University',
            'code': 'harvard',
            'website': 'https://www.harvard.edu',
            'opportunities_url': 'https://www.harvard.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'Yale University',
            'code': 'yale',
            'website': 'https://www.yale.edu',
            'opportunities_url': 'https://www.yale.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'Princeton University',
            'code': 'princeton',
            'website': 'https://www.princeton.edu',
            'opportunities_url': 'https://www.princeton.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'Columbia University',
            'code': 'columbia',
            'website': 'https://www.columbia.edu',
            'opportunities_url': 'https://www.columbia.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'Cornell University',
            'code': 'cornell',
            'website': 'https://www.cornell.edu',
            'opportunities_url': 'https://www.cornell.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'Dartmouth College',
            'code': 'dartmouth',
            'website': 'https://www.dartmouth.edu',
            'opportunities_url': 'https://www.dartmouth.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'Brown University',
            'code': 'brown',
            'website': 'https://www.brown.edu',
            'opportunities_url': 'https://www.brown.edu/opportunities',
            'is_ivy_league': True,
        },
        {
            'name': 'University of Pennsylvania',
            'code': 'upenn',
            'website': 'https://www.upenn.edu',
            'opportunities_url': 'https://www.upenn.edu/opportunities',
            'is_ivy_league': True,
        },
    ]
    
    for uni_data in universities:
        uni, created = University.objects.get_or_create(
            code=uni_data['code'],
            defaults=uni_data
        )
        if created:
            print(f"Created university: {uni.name}")
        else:
            print(f"University already exists: {uni.name}")


def create_superuser():
    """Create superuser if it doesn't exist"""
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User',
            user_type='admin'
        )
        print("Created superuser: admin")
    else:
        print("Superuser already exists")


def main():
    print("Initializing database...")
    create_universities()
    create_superuser()
    print("Database initialization complete!")


if __name__ == '__main__':
    main()