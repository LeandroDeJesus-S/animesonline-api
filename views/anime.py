from flask import request
from flask.json import jsonify
from flask_pydantic_spec import Response
from pydantic import ValidationError, PydanticValueError
from models import Animes, Anime, JsonResponseMessage, Headers
from flask import Blueprint
from api_spec import spec
from database import db
from sqlalchemy import text
from utils.authutils import validate_auth
from pprint import pprint
from sqlalchemy.exc import DatabaseError, DataError, IntegrityError, OperationalError

anime_bp = Blueprint('anime', __name__)
spec.register(anime_bp)
ANIME_COLS = ('id', 'name', 'year', 'sinopse', 'categories', 'rate', 'url')

@anime_bp.route('/anime', methods=['GET'])
@spec.validate(resp=Response(HTTP_200=Animes, 
                             HTTP_404=JsonResponseMessage, 
                             HTTP_400=JsonResponseMessage, 
                             HTTP_422=JsonResponseMessage, 
                             HTTP_500=JsonResponseMessage))
def list_animes():
    try:
        query_result = db.session.execute(text(
            f"SELECT {', '.join(ANIME_COLS)} FROM anime"
        )).fetchall()
        
        if not query_result:
            msg = 'Não há animes para exibir'
            return JsonResponseMessage(status_code=404, message_type='error', message=msg).dict(), 404
        
        resp = [dict(zip(ANIME_COLS, row)) for row in query_result]
        return jsonify(Animes(animes=resp).dict()), 200
    
    except DataError as e:
        return JsonResponseMessage(status_code=422, message_type='error', message=str(e)).dict(), 422
    
    except DatabaseError as e:
        return JsonResponseMessage(status_code=400, message_type='error', message=str(e)).dict(), 400
    
    except Exception as e:
        return JsonResponseMessage(status_code=500, message_type='error', message=str(e)).dict(), 500


@anime_bp.route('/anime', methods=['POST'])
@spec.validate(body=Anime, headers=Headers, resp=Response(HTTP_201=JsonResponseMessage, 
                                            HTTP_404=JsonResponseMessage, 
                                            HTTP_400=JsonResponseMessage, 
                                            HTTP_403=JsonResponseMessage, 
                                            HTTP_422=JsonResponseMessage, 
                                            HTTP_500=JsonResponseMessage))
def add_anime():
    if not validate_auth(request.headers):
        msg = 'Acesso não autorizado.'
        return JsonResponseMessage(status_code=403, message_type='error', message=msg).dict(), 403
    
    context = request.context.body.dict()  # type: ignore
    if not context:
        msg = 'Dados inválidos'
        return JsonResponseMessage(status_code=404, message_type='error', message=msg).dict(), 404
    
    try:
        id = context.get('id')
        id_query = ':id, ' if id is not None else ''
        name = context.get('name')
        year = context.get('year')
        sinopse = context.get('sinopse')
        categories = context.get('categories')
        rate = context.get('rate')
        url = context.get('url')

        query_data = {
            'name': name, 
            'year':year, 
            'sinopse': sinopse, 
            'categories':categories, 
            'rate':rate, 
            'url':url
        }
        if id is not None:
            query_data.update({'id': id})

        db.session.execute(
            text(
                f"INSERT INTO anime ({id_query[1:]}name, year, sinopse, categories, rate, url) \
                    VALUES ({id_query}:name, :year, :sinopse, :categories, :rate, :url)"
            ),
            query_data
        )

        db.session.commit()
        return JsonResponseMessage(
            status_code=201, 
            message_type='success', 
            message='Anime adicionado com sucesso'
        ).dict(), 201
    
    except (DataError, IntegrityError, ValidationError, PydanticValueError) as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=422, 
            message_type='error', 
            message=str(e)
        ).dict(), 422
    
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


@anime_bp.route('/anime/<int:anime_id>', methods=['GET'])
@spec.validate(resp=Response(HTTP_200=Anime, HTTP_404=JsonResponseMessage, HTTP_422=JsonResponseMessage))
def get_anime(anime_id: int):
    try:
        query_result = db.session.execute(
            text(
                f"SELECT {', '.join(ANIME_COLS)} FROM anime WHERE id = :id LIMIT 1"
            ), 
            {'id': anime_id}
        ).fetchone()

        if not query_result:
            return JsonResponseMessage(
                status_code=404, 
                message_type='info', 
                message='Anime não encontrado'
            ).dict(), 404
        
        resp = dict(zip(ANIME_COLS, query_result))
        return jsonify(Anime(**resp).dict()), 200

    except (DataError, IndexError) as e:
        return JsonResponseMessage(
            status_code=422, 
            message_type='error', 
            message=str(e)
        ).dict(), 422
    
    except DatabaseError as e:
        return JsonResponseMessage(
            status_code=404, 
            message_type='error', 
            message=str(e)
        ).dict(), 404


@anime_bp.route('/anime/<int:anime_id>', methods=['PUT'])
@spec.validate(body=Anime, headers=Headers, resp=Response(HTTP_404=JsonResponseMessage, 
                                         HTTP_200=JsonResponseMessage, 
                                         HTTP_422=JsonResponseMessage, 
                                         HTTP_500=JsonResponseMessage))
def modify_anime(anime_id: int):
    if not validate_auth(request.headers):
        msg = 'Acesso não autorizado.'
        return JsonResponseMessage(status_code=403, message_type='error', message=msg).dict(), 403

    data = request.context.body.dict()  # type: ignore
    if not data:
        return JsonResponseMessage(
            status_code=404, 
            message_type='info', 
            message='Dados inválidos'
        ).dict(), 404
    
    columns = list(data.keys())
    values = data.copy()
    values.update({'id': anime_id})


    mask = ', '.join(f'{c} = :{c}' for c in columns)
    sql_query = f"UPDATE anime SET {mask} WHERE id = :id"

    try:
        db.session.execute(
            text(sql_query),
            values
        )
        db.session.commit()
        return JsonResponseMessage(
            status_code=200, 
            message_type='success', 
            message='Anime alterado com sucesso'
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


@anime_bp.route('/anime/<int:anime_id>', methods=['DELETE'])
@spec.validate(headers=Headers, resp=Response(HTTP_400=JsonResponseMessage,
                                              HTTP_403=JsonResponseMessage,
                                              HTTP_404=JsonResponseMessage,
                                              HTTP_422=JsonResponseMessage,
                                              HTTP_500=JsonResponseMessage))
def delete_anime(anime_id: int):
    if not validate_auth(request.headers):
        msg = 'Acesso não autorizado.'
        return JsonResponseMessage(status_code=403, message_type='error', message=msg).dict(), 403
    
    try:
        db.session.execute(
            text("DELETE FROM anime WHERE id = :id"),
            {'id': anime_id}
        )

        db.session.commit()
        return '', 204  
    
    except OperationalError as e:
        db.session.rollback()
        return JsonResponseMessage(
            status_code=404, 
            message_type='error', 
            message=str(e)
        ).dict(), 404
    
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
