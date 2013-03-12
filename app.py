#coding: utf-8

from flask import *
from logging.handlers import *
from flask_twitter.TwitterPlugin import *
import pymongo
import random
import urllib
from settings import *
from sender import send


app = Flask(__name__);

formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
)
error_log = os.path.join(app.root_path, 'logs/error.log')
error_file_handler = RotatingFileHandler(
    error_log, maxBytes=100000, backupCount=10
)    
error_file_handler.setLevel(logging.ERROR)
error_file_handler.setFormatter(formatter)
app.logger.addHandler(error_file_handler)

URL_BASE = "http://search.naver.jp/image"
BASE_PARAM = {
    "q": "",
    "sm": "sbx_hty.image",
};

@app.before_request
def before_request():
    g.conn = pymongo.Connection(host=DB_HOST);
    g.db = g.conn[DB_NAME]; 

@app.teardown_request
def teardown_request(exception):
    g.conn.disconnect();
    g.db = None;

@app.route("/")
def index():
    return render_template("home.html");

@app.route("/<int:id>")
def button_index(id):
    button = g.db.buttons.find_one({"_id": id});
    return render_template("index.html", button=button, image=button["images"][random.randint(0, len(button["images"]) - 1)]);

@app.route("/add", methods=["POST", "GET"])
def add():
    if (request.method == "POST"):
        id = g.db.buttons.count();
        name = request.form["name"];
        description = request.form.get("description");
        g.db.buttons.insert({"_id": id, "name": name, "description": description});
        query = BASE_PARAM;
        query["q"] = name.encode("utf-8");
        send("CharactorImageCrawler", URL_BASE + "?" + urllib.urlencode(query), id);
        send("LogoCrawler", "", id, name);
        return redirect("/add-result/" + str(id))
    return render_template("add.html")

@app.route("/add-result/<int:id>")
def add_result(id):
    return render_template("add_result.html", id=id)

@app.route("/kawaii/<int:id>")
@twitter_login
def kawaii(id, api=None):
    button = g.db.buttons.find({"_id": id});
    name = button.name;
    urls = button.images; 
    text = u"%sちゃんかわいい via %sちゃんかわいいぼたん http://rikka.contents4you.com/%s %s" % (name, name, name, urls[random.randint(0, len(urls) - 1)]) + u"　" * random.randint(0, 20)
    api.update_status(text);
    return redirect("/");

@app.route("/twitter/callback")
@twitter_callback
def callback(api=None):
    return make_response("test");

if __name__ == "__main__":
    app.debug = True;
    app.run();
