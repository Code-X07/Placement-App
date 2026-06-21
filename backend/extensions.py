from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from celery import Celery

bcrypt = Bcrypt()
jwt = JWTManager()
mail = Mail()
celery = Celery()
