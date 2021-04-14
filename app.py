from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from db.db import get_mysql_connection
from config.config import Config
import pandas as pd
import numpy as np
from resources.user import UserRegister, jwt_blocklist, UserLoginResource, UserLogoutResource 
from resources.movie import MovieSearchResource, MovieResource, MovieRecommandResource, MovieOrderResource
app = Flask(__name__)

# 환경 변수 설정.
app.config.from_object(Config)

# JWT 환경 설정.
jwt = JWTManager(app)

@jwt.token_in_blocklist_loader
def check_if_token_is_revoked(jwt_header, jwt_payload) :
    jti = jwt_payload['jti']
    return jti in jwt_blocklist

# api 설정.
api = Api(app)

# 경로랑 리소스 연결.
api.add_resource(MovieOrderResource, '/v1/movie/order')
api.add_resource(MovieSearchResource, '/v1/movie/reviews')
api.add_resource(MovieResource, '/v1/movie/reviews/search','/v1/movie/reviews/add') # 경로에 변수 처리
api.add_resource(MovieRecommandResource, '/v1/movie/<int:user_id>/recommand')

api.add_resource(UserRegister, '/v1/users')
api.add_resource(UserLoginResource, '/v1/users/login', '/v1/users/<int:user_id>/my')
api.add_resource(UserLogoutResource, '/v1/users/logout')

if __name__ == '__main__' :
    app.run()