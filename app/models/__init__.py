# app/models/__init__.py
from app.models.user import User
from app.models.pet import Pet
from app.models.caregiver import CaregiverProfile
from app.models.booking import Booking
from app.models.review import Review

# This allows all models to be imported from app.models
__all__ = ['User', 'Pet', 'CaregiverProfile', 'Booking', 'Review']