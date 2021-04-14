from flask import request
from flask_restful import Resource
from http import HTTPStatus
from db.db import get_mysql_connection
from mysql.connector import Error
from utils import hash_password, check_password
from email_validator import EmailNotValidError, validate_email
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from flask_jwt_extended import get_jti
jwt_blocklist = set()

# 회원가입 API
class UserRegister(Resource) :
    def post(self) :

        data = request.get_json()

        # 0. 데이터가 전부 다 있는지 체크
        if 'name' not in data or 'email' not in data or 'password' not in data :
            return {'err_code' : 1}, HTTPStatus.BAD_REQUEST

        # 1. 이메일이 유효한지 체크
        try :
            validate_email(data['email'])

        except EmailNotValidError as e :
            print(str(e))
            return {'err_code' : 3}, HTTPStatus.BAD_REQUEST

        # 2. 비밀번호 길이체크 및 암호화
        if len(data['password']) < 4 or len(data['password']) > 20 :
            return {'err_code' : 2}, HTTPStatus.BAD_REQUEST

        password = hash_password(data['password'])

        print(password)

        # 3. 데이터베이스에 저장.
        ## 실습. 디비에 데이터 인서트 시, 유니크로 인해서 데이터가
        ## 들어가지 않는 경우를 대비하여, 코드를 수정하세요.

        try :
                
            connection = get_mysql_connection()
            cursor = connection.cursor()
            query = """ insert into yhdb.movie_user
                        (email, password, name, gender) 
                        values(%s, %s, %s, %s);"""

            param = (data['email'], password, data['name'], data['gender'])
            
            cursor.execute(query, param)
            connection.commit()

            # 디비에 데이터를 저장한 후, 저장된 아이디값을 받아온다.
            user_id = cursor.lastrowid
            print(user_id)

        except Error as e :
            print(str(e))
            return {'err_code' : 4 }, HTTPStatus.NOT_ACCEPTABLE

        cursor.close()
        connection.close()

        # JWT를 이용해서 인증토큰을 생성해준다.
        access_token = create_access_token(identity=user_id)

        return {'token' : access_token}, HTTPStatus.OK

class UserLoginResource(Resource) :
    # 로그인 API
    def post(self) :
        
        # 1. 클라이언트로부터 이메일과 비밀번호를 받아온다.
        data = request.get_json()
        if 'email' not in data or 'password' not in data :
            return {'err_code' : 1}, HTTPStatus.BAD_REQUEST

        # 2. 이메일 벨리데이션 체크
        try :
            validate_email(data['email'])

        except EmailNotValidError as e :
            print(str(e))
            return {'err_code' : 2}, HTTPStatus.BAD_REQUEST

        # 3. 비밀번호가 맞는지 체크하기 위해서 데이터 베이스에서 위의 이메일로
        #    유저 정보를 가져온다. (select)
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)
        query = """select id, password from yhdb.movie_user
                    where email = %s;"""

        param = (data['email'], )
            
        cursor.execute(query, param)
        records = cursor.fetchall()
        print(records)

        # 3-1. 회원가입이 안된 이메일로 요청했을때는, record에 데이터가 없으니까
        #      클라이언트에게 응답한다.
        if len(records) == 0 :
            return {'err_code' : 3}, HTTPStatus.BAD_REQUEST

        # 4. 위에서 가져온 디비에 저장되어있는 비밀번호와, 클라이언트로부터
        #    받은 비밀번호를 암호화 한것과 비교한다.
        password = data['password']
        hashed = records[0]['password']
        ret = check_password(password, hashed)

        # 5. 같으면 클라이언트에 200 리턴
        if ret is True :

            user_id = records[0]['id']
            access_token = create_access_token(identity = user_id)

            return {'token' : access_token}, HTTPStatus.OK

        # 6. 다르면, 에러 리턴
        else :
            return {'err_code' : 4}, HTTPStatus.BAD_REQUEST

    # 내정보 가져오는 API
    @jwt_required()
    def get(self, user_id) :

        # 토큰에서 유저 아이디 가져온다.
        token_user_id = get_jwt_identity()

        if token_user_id != user_id :
            return {'err_code' : 1}, HTTPStatus.UNAUTHORIZED

        # 1. 데이터베이스에서 쿼리해서 유저정보 가져온다.
        connection = get_mysql_connection()
        cursor = connection.cursor(dictionary=True)

        query = """ select u.email, u.name, u.gender, m.title, r.rating
                    from rating r
                    join movie m on m.id = r.item_id
                    join movie_user u on u.id = r.user_id
                    where u.id = %s; """

        param = (user_id, )

        cursor.execute(query, param)
        records = cursor.fetchall()  

        cursor.close()
        connection.close()

        # 2. 유저정보 없으면, 클라이언트에 유저정보 없다고 리턴
        if len(records) == 0 :
            return {'err_code' : 2}, HTTPStatus.BAD_REQUEST

        # 3. 있으면, 해당유저 정보를 리턴
        else :
            return {'ret' : records}, HTTPStatus.OK


# 로그아웃 API 만들기
class UserLogoutResource(Resource) :
    @jwt_required()
    def post(self) :

        jti = get_jwt()['jti']
        jwt_blocklist.add(jti)

        return {'message' : 'Successful Logout!'}, HTTPStatus.OK