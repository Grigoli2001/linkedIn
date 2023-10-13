from website import create_app
from website.root import close_db
import subprocess
app = create_app()


@app.teardown_appcontext
def app_teardown(exception):
    close_db(exception)
subprocess.run(["python", "website\APIs\insert_products.py"])
if __name__ =='__main__':
    app.run(host="127.0.0.1",port=2000,debug=True)

