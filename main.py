from website import create_app
from website.root import close_db
import subprocess
import logging
from flask_debugtoolbar import DebugToolbarExtension
from flask import g, request
import time

app = create_app()

# Configure logging settings
logging.basicConfig(filename='app.log', level=logging.DEBUG)

toolbar = DebugToolbarExtension(app)


@app.teardown_appcontext
def app_teardown(exception):
    close_db(exception)
subprocess.run(["python", "website\APIs\insert_jobs.py"])
@app.before_request
def before_request():
    g.start_time = time.time()
    logging.info(f"Request started: {request.url}")

@app.after_request
def after_request(response):
    elapsed_time = time.time() - g.start_time
    logging.info(f"Request finished in {elapsed_time:.4f} seconds")
    return response

if __name__ =='__main__':
    app.run(host="127.0.0.1",port=2000,debug=True)

