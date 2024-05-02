from flask import Blueprint
from flask.json import jsonify
from sqlalchemy.exc import DatabaseError, DataError
from flask_pydantic_spec import Response
from models import Seasons, Season, JsonResponseMessage
from api_spec import spec
from sqlalchemy import text
from database import db

season_bp = Blueprint('season', __name__)
spec.register(season_bp)


@season_bp.route('/anime/<int:anime_id>/season', methods=['GET'])
@spec.validate(resp=Response(HTTP_200=Seasons, 
                             HTTP_404=JsonResponseMessage,
                             HTTP_422=JsonResponseMessage,
                             HTTP_500=JsonResponseMessage,
                             HTTP_400=JsonResponseMessage))
def list_seasons(anime_id: int):
    try:
        query_result = db.session.execute(
            text(
                'SELECT season, count(*) as episodes \
                    FROM episode WHERE anime_id = :aid GROUP BY season'
            ), 
            {'aid': anime_id},
        ).fetchall()

        if not query_result:
            return JsonResponseMessage(
            status_code=404, 
            message_type='info', 
            message='Há episódios para exibir'
        ).dict(), 404
        
        columns = list(Season.schema()['properties'].keys())
        resp = [dict(zip(columns, row)) for row in query_result]
        return jsonify(Seasons(seasons=resp).dict()), 200

    except DataError as e:
        return JsonResponseMessage(
            status_code=422, 
            message_type='error', 
            message=str(e)
        ).dict(), 422
    
    except DatabaseError as e:
        return JsonResponseMessage(
            status_code=400, 
            message_type='error', 
            message=str(e)
        ).dict(), 400
    
    except Exception as e:
        return JsonResponseMessage(
            status_code=500, 
            message_type='error', 
            message=str(e)
        ).dict(), 500


@season_bp.route('/anime/<int:anime_id>/season/<int:season_num>', methods=['GET'])
@spec.validate(resp=Response(HTTP_200=Seasons, 
                             HTTP_404=JsonResponseMessage, 
                             HTTP_422=JsonResponseMessage, 
                             HTTP_500=JsonResponseMessage, 
                             HTTP_400=JsonResponseMessage))
def get_season(anime_id: int, season_num: int):
    try:
        query_result = db.session.execute(
            text(
                'SELECT season, count(*) as episodes \
                    FROM episode WHERE anime_id = :aid and season = :s \
                        GROUP BY season'
            ), 
            {'aid': anime_id, 's': season_num}
        ).fetchall()

        if not query_result:
            return JsonResponseMessage(
            status_code=404, 
            message_type='info', 
            message='Não há episódio para exibir'
        ).dict(), 404
        
        columns = list(Season.schema()['properties'].keys())
        resp = [dict(zip(columns, row)) for row in query_result]
        return jsonify(Seasons(seasons=resp).dict()), 200

    except DataError as e:
        return JsonResponseMessage(
            status_code=422, 
            message_type='error', 
            message=str(e)
        ).dict(), 422

    except DatabaseError as e:
        return JsonResponseMessage(
            status_code=400, 
            message_type='error', 
            message=str(e)
        ).dict(), 400
    
    except Exception as e:
        return JsonResponseMessage(
            status_code=500, 
            message_type='error', 
            message=str(e)
        ).dict(), 500
