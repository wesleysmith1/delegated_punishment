from os import environ

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']
EXTENSION_APPS = [
    'delegated_punishment',
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': environ.get('DATABASE', 'django_db'),
        'USER': environ.get('DB_USER', 'postgres'),
        'PASSWORD': environ.get('DB_PASSWORD', 'password'),
        'HOST': 'localhost',
        'PORT': '5432'
    }
}
"""
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'logfile': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "./logs/debug/logfile",
            'maxBytes': 50000,
            'backupCount': 2,
            'formatter': 'standard',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'WARN',
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'delegated_punishment': {
            'handlers': ['console', 'logfile'],
            'level': 'DEBUG',
        },
    }
}
"""

SESSION_CONFIGS = [
    dict(
        name='delegated_punishment', 
        display_name="Delegated Punishment Game",
        use_browser_bots=False,
        num_demo_participants=6,
        app_sequence=['welcome', 'delegated_punishment', 'survey'],
        session_identifier=0,
        civilian_income_config=1,
        tutorial_civilian_income=40,
        tutorial_officer_bonus=260,
        grain_conversion=.1,
        showup_payment=7,
        participant_endowment=10,
        balance_update_rate=250,
        skip_to_round=1,
    ),
    dict(
        name='survey',
        display_name='survey',
        num_demo_participants=5,
        app_sequence=['survey'],
    ),
    dict(
        name='welcome',
        display_name='welcome',
        num_demo_participants=5,
        app_sequence=['welcome'],
    ),
]

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True
DEBUG = True


ROOMS = [
    dict(
        name='delegated_punishment',
        display_name='Delegated Punishment',
        participant_label_file=None,
    ),
    dict(name='live_demo', display_name='Room for live demo (no participant labels)'),
]

AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL', 'DEMO')

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD', 'password')

OTREE_PRODUCTION = environ.get('OTREE_PRODUCTION', True)

DEMO_PAGE_INTRO_HTML = """
Here are some oTree games.
"""

# don't share this with anybody.
SECRET_KEY = '6lertt4wlb09zj@4wyuy-p-6)i$vh!ljwx&r9bti6kgw54k-h8'

INSTALLED_APPS = ['otree']

# ROOT_URLCONF = 'urls'
