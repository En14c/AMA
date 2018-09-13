from flask import render_template
from flask_login import login_required
from app.models import AppPermissions
from . import main

@main.app_context_processor
def templates_add_app_permissions():
    return dict(app_permissions=AppPermissions)

@main.route('/')
@login_required
def home():
    return render_template('main/home.html')

