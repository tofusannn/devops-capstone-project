"""
Package: service
Package for the application models and service routes
This module creates and configures the Flask app and sets up the logging
and SQL database
"""
import os
import sys
from flask import Flask
from flask_cors import CORS
from flask_talisman import Talisman
from service import config
from service.common import log_handlers

# Create Flask application
app = Flask(__name__)
app.config.from_object(config)

# Keep local development and automated test traffic on HTTP. When deployed behind
# an HTTPS ingress, set FORCE_HTTPS=true to enable redirects and HSTS.
Talisman(
    app,
    force_https=os.getenv("FORCE_HTTPS", "false").lower() == "true",
    content_security_policy={
        "default-src": "'self'",
        "object-src": "'none'",
        "frame-ancestors": "'none'",
    },
    frame_options="DENY",
    referrer_policy="no-referrer",
)

# Set CORS_ORIGINS to a comma-separated list of trusted browser origins in
# production. Wildcard default is intended for the training lab's public API.
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
CORS(app, resources={r"/accounts.*": {"origins": cors_origins}})

# Import the routes After the Flask app is created
# pylint: disable=wrong-import-position, cyclic-import, wrong-import-order
from service import routes, models  # noqa: F401 E402

# pylint: disable=wrong-import-position
from service.common import error_handlers, cli_commands  # noqa: F401 E402

# Set up logging for production
log_handlers.init_logging(app, "gunicorn.error")

app.logger.info(70 * "*")
app.logger.info("  A C C O U N T   S E R V I C E   R U N N I N G  ".center(70, "*"))
app.logger.info(70 * "*")

try:
    models.init_db(app)  # make our database tables
except Exception as error:  # pylint: disable=broad-except
    app.logger.critical("%s: Cannot continue", error)
    # gunicorn requires exit code 4 to stop spawning workers when they die
    sys.exit(4)

app.logger.info("Service initialized!")
