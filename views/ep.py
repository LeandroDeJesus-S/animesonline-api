from flask import request
from flask.json import jsonify
from sqlalchemy.exc import DatabaseError, DataError
from sqlalchemy import text
from flask_pydantic_spec import Response
from models import JsonResponseMessage, Episode, SeasonEpisodes, Headers
from flask import Blueprint
from api_spec import spec
from utils.authutils import validate_auth
from pydantic import ValidationError
from database import db

ep_bp = Blueprint('ep', __name__)
spec.register(ep_bp)
EP_COLS = ['id', 'anime_id', 'number', 'date', 'season', 'url']


@ep_bp.route('/anime/<int:anime_id>/season/<int:season_num>/episode', methods=['GET'])
@spec.validate(resp=Response(HTTP_200=SeasonEpisodes, 
                             HTTP_404=JsonResponseMessage, 
                             HTTP_422=JsonResponseMessage, 
                             HTTP_500=JsonResponseMessage))
def list_eps(anime_id: int, season_num: str):
    try:
        query_result = db.session.execute(
            text(
                f'SELECT {", ".join(EP_COLS)} \
                    FROM episode WHERE anime_id = :anime_id AND season = :s \
                        ORDER BY date, number'
            ),
            {'anime_id': anime_id, 's': season_num}
        ).fetchall()
        query_result = list(map(lambda x: (x[0], x[1], x[2], x[3], x[4], x[5]), query_result))

        if not query_result:
            msg = 'Não há episódios para exibir'
            return JsonResponseMessage(status_code=404, message_type='error', message=msg).dict(), 404

        resp = [Episode(**dict(zip(EP_COLS, row))) for row in query_result]
        return jsonify(SeasonEpisodes(season=season_num, episodes=resp).dict()), 200

    except DataError as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=422, message_type='error', message=str(e)).dict(), 422
    
    except DatabaseError as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=404, message_type='error', message=str(e)).dict(), 404

    except Exception as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=500, message_type='error', message=str(e)).dict(), 500


@ep_bp.route('/anime/<int:anime_id>/season/<int:season_num>/episode', methods=['POST'])
@spec.validate(body=Episode, headers=Headers, resp=Response(HTTP_201=JsonResponseMessage, 
                                                            HTTP_400=JsonResponseMessage, 
                                                            HTTP_403=JsonResponseMessage, 
                                                            HTTP_422=JsonResponseMessage, 
                                                            HTTP_500=JsonResponseMessage, 
                                                            HTTP_404=JsonResponseMessage))
def add_ep(anime_id: int, season_num: int):
    if not validate_auth(request.headers):
        msg = 'Acesso não autorizado.'
        return JsonResponseMessage(status_code=403, message_type='error', message=msg).dict(), 403
    
    data = request.context.body.dict()  # type: ignore
    id = data.get('id')
    anime_id = data.get('anime_id')
    number = data.get('number')
    season = data.get('season')
    date = data.get('date')
    url = data.get('url')

    has_none = list(filter(lambda x: x is None, data.values()))
    if not data or has_none or season != season_num:
        msg = 'Dados inválidos'
        return JsonResponseMessage(status_code=400, message_type='error', message=msg).dict(), 400
    
    try:
        sql = f'INSERT INTO episode ({", ".join(EP_COLS)}) VALUES (:id, :aid, :n, :d, :s, :u)'
        val = {'id': id, 'aid': anime_id, 'n': str(number), 'd': date, 's': season, 'u': url}

        db.session.execute(
            text(sql), val
        )

        db.session.commit()
        return JsonResponseMessage(
            status_code=201, 
            message_type='success', 
            message='Episódio adicionado com sucesso'
        ).dict(), 201
    
    except DataError as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=422, message_type='error', message=str(e)).dict(), 422

    except DatabaseError as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=404, message_type='error', message=str(e)).dict(), 404

    except Exception as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=500, message_type='error', message=msg).dict(), 500


@ep_bp.route('/anime/<int:anime_id>/season/<int:season_num>/episode/<int:ep_num>', methods=['DELETE'])
@spec.validate(headers=Headers, resp=Response(HTTP_404=JsonResponseMessage, 
                                              HTTP_403=JsonResponseMessage, 
                                              HTTP_422=JsonResponseMessage, 
                                              HTTP_500=JsonResponseMessage))
def delete_ep(anime_id: int, season_num: int, ep_num: int):
    if not validate_auth(request.headers):
        msg = 'Acesso não autorizado.'
        return JsonResponseMessage(status_code=403, message_type='error', message=msg).dict(), 403
    
    try:
        db.session.execute(
            text('DELETE FROM episode WHERE anime_id = :aid AND season = :s AND number = :n'),
            {'aid': anime_id, 's': season_num, 'n': str(ep_num)}
        )
        db.session.commit()
        return '', 204
    
    except DataError as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=422, 
            message_type='error', 
            message=str(e)
        ).dict(), 422
    
    except DatabaseError as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=404, 
            message_type='error', 
            message=str(e)
        ).dict(), 404

    except Exception as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=500, 
            message_type='error', 
            message=str(e)
        ).dict(), 500


@ep_bp.route('/anime/<int:anime_id>/season/<int:season_num>/episode/<int:ep_num>', methods=['PUT'])
@spec.validate(body=Episode, headers=Headers, resp=Response(HTTP_200=JsonResponseMessage, 
                                                            HTTP_404=JsonResponseMessage, 
                                                            HTTP_403=JsonResponseMessage, 
                                                            HTTP_422=JsonResponseMessage, 
                                                            HTTP_500=JsonResponseMessage))
def modify_ep(anime_id: int, season_num: int, ep_num: int):
    if not validate_auth(request.headers):
        msg = 'Acesso não autorizado.'
        return JsonResponseMessage(status_code=403, message_type='error', message=msg).dict(), 403
    
    data = request.context.body.dict()  # type: ignore
    
    columns = tuple(data.keys())
    values = data.copy()
    values.update({'aid': anime_id, 's': season_num, 'n': str(ep_num)})
 
    mask = ', '.join(f'{c} = :{c}' for c in columns)
    sql_query = f"UPDATE episode SET {mask} WHERE anime_id = :aid AND season = :s AND number = :n"

    try:
        db.session.execute(
            text(sql_query),
            values
        )
        db.session.commit()
        return JsonResponseMessage(
            status_code=200, 
            message_type='success', 
            message='Episódio modificado com sucesso'
        ).dict(), 200
    
    except DataError as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=422, 
            message_type='error', 
            message=str(e)
        ).dict(), 422
    
    except DatabaseError as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=404, 
            message_type='error', 
            message=str(e)
        ).dict(), 404

    except Exception as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=500, 
            message_type='error', 
            message=str(e)
        ).dict(), 500


@ep_bp.route('/anime/<int:anime_id>/season/<int:season_num>/episode/<int:ep_num>', methods=['GET'])
@spec.validate(resp=Response(HTTP_200=Episode, 
                             HTTP_404=JsonResponseMessage, 
                             HTTP_422=JsonResponseMessage, 
                             HTTP_500=JsonResponseMessage, 
                             HTTP_400=JsonResponseMessage))
def get_ep(anime_id: int, season_num: str, ep_num: int):
    try:
        query_result = db.session.execute(
            text('SELECT * FROM episode WHERE anime_id = :aid AND season = :s and number = :n'),
            {'aid': anime_id, 's': season_num, 'n': str(ep_num)}
        ).fetchone()
        
        if not query_result:
            return JsonResponseMessage(
            status_code=404, 
            message_type='info', 
            message='Não há episódios para exibir'
        ).dict(), 404
        
        resp = Episode(**dict(zip(EP_COLS, query_result)))
        return jsonify(resp.dict()), 200

    except DataError as e:
        db.session.rollback()
        return JsonResponseMessage(status_code=422, message_type='error', message=str(e)).dict(), 422
    
    except DatabaseError as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=400, 
            message_type='error', 
            message=str(e)
        ).dict(), 400
    
    except Exception as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=500, 
            message_type='error', 
            message=str(e)
        ).dict(), 500
