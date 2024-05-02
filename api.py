from flask import Flask
# from flask_cors import CORS
from flask.json.provider import DefaultJSONProvider
from views.anime import anime_bp
from views.ep import ep_bp
from views.season import season_bp
from api_spec import spec
from database import db
import os
"""
/anime                                                                  GET - POST
/anime/<int:anime_id>                                                   GET - PUT - DELETE

/anime/<int:anime_id>/season                                            GET - POST
/anime/<int:anime_id>/season/<int:season_num>                           GET - POST - DELETE

/anime/<int:anime_id>/season/<int:season_num>/episode                   GET - POST
/anime/<int:anime_id>/season/<int:season_num>/episode/<int:ep_num>      GET - PUT - DELETE
"""

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv('DATABASEURI')
db.init_app(app)
spec.register(app)
DefaultJSONProvider.ensure_ascii = False

app.register_blueprint(anime_bp)
app.register_blueprint(season_bp)
app.register_blueprint(ep_bp)

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
