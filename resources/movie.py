from flask import request
from flask_restful import Resource
from http import HTTPStatus
import simplejson
from db.db import get_mysql_connection
import pandas as pd
import numpy as np
from pandas import DataFrame



# JWT 라이브러리
from flask_jwt_extended import jwt_required, get_jwt_identity

# 우리가 이 파일에서 작성하는 클래스는,
# 플라스크 프레임워크에서, 경로랑 연결시킬 클래스 입니다.
# 따라서, 클래스 명 뒤에, Resource 클래스를 상속받아야 합니다.
# 플라스크 프레임워크의 레퍼런스 사용법에 나와 있습니다.

class MovieOrderResource(Resource) :
    # get 메소드로 연결시킬 함수  작성.
    def get(self) :
        # movie 테이블에 저장되어 있는 모든 정보를 정렬해서 가져오는 함수
        # 1. DB 커넥션을 가져온다.
        data = request.get_json()

        if 'order' not in data :
            return {'message' : 'Parmeter error'}, HTTPStatus.BAD_REQUEST

        connection = get_mysql_connection()

        print(connection)

        # 2. 커넥션에서 커서를 가져온다.
        cursor = connection.cursor(dictionary=True)

        # 3. 쿼리문을 작성한다.
        query = """select m.title, count(r.rating) as reviews, round(avg(r.rating),2) as average
                    from rating r
                    join movie m on r.item_id = m.id
                    group by m.title 
                    order by %s desc
                    limit %s, 25;"""
        # print(data['order'])
        param = (data['order'],data['offset'])

        # 4. SQL 실행
        cursor.execute(query,param)

        # 5. 데이터를 페치한다.
        records = cursor.fetchall()

        # 6. 커서와 커넥션을 닫아준다.
        cursor.close()
        connection.close()

        # 7. 클라이언트에 리스폰스 한다.
        return {'ret':records }, HTTPStatus.OK

class MovieSearchResource(Resource) :
    def get(self) :
    
        # movie 테이블에 저장되어 있는 정보를 검색해서 가져오는 함수
        # 1. DB 커넥션을 가져온다.
        data = request.get_json()

        if 'title' not in data :
            return {'message' : 'Parmeter Error'}, HTTPStatus.BAD_REQUEST
        
        connection = get_mysql_connection()

        print(connection)

        # 2. 커넥션에서 커서를 가져온다.
        cursor = connection.cursor(dictionary=True)

        # 3. 쿼리문을 작성한다.
        query = """select u.name, u.gender, r.rating
                   from rating r
                   join movie_user u on r.user_id = u.id
                   join movie m on m.id = r.item_id
                   where m.title = %s limit %s, 25;"""

        param = (data['title'],data['offset'])
        # 4. SQL 실행
        cursor.execute(query,param)

        # 5. 데이터를 페치한다.
        records = cursor.fetchall()

        # 6. 커서와 커넥션을 닫아준다.
        cursor.close()
        connection.close()

        # 7. 클라이언트에 리스폰스 한다.
        if len(records) ==0 :
            return {'message' : 'Title name error'}, HTTPStatus.NOT_FOUND
        else :
            return {'ret':records}, HTTPStatus.OK


class MovieResource(Resource) :

    def get(self) :
        # 영화 리뷰를 작성하기 위한 영화 정보를 검색하는 함수
        # 1. DB 커넥션을 가져온다.
        data = request.get_json()

        if 'title' not in data :
            return {'message' : 'Parmeter Error'}, HTTPStatus.BAD_REQUEST
        
        connection = get_mysql_connection()

        print(connection)

        # 2. 커넥션에서 커서를 가져온다.
        cursor = connection.cursor(dictionary=True)

        # 3. 쿼리문을 작성한다.
        query = """select m.id, m.title, count(r.rating) as reviews, round(avg(r.rating),2) as average
                    from rating r
                    join movie m on r.item_id = m.id
                    where m.title = %s
                    group by m.title;"""

        param = (data['title'],)
        # 4. SQL 실행
        cursor.execute(query,param)

        # 5. 데이터를 페치한다.
        records = cursor.fetchall()

        # 6. 커서와 커넥션을 닫아준다.
        cursor.close()
        connection.close()

        # 7. 클라이언트에 리스폰스 한다.
        if len(records) ==0 :
            return {'message' : 'Title name error'}
        else :
            return {'ret':records}, HTTPStatus.OK

    @jwt_required() # 로그인한 유저만 이 API 이용 할 수 있다.
    # 위에서 봤던 영화정보의 id를 받아와 리뷰를 작성하는 함수
    def post(self) :
        # 1. 클라이언트가 요청한 request의 body에 있는 json 데이터를 가져오기
        data = request.get_json()

        # 2. 필수 항목이 있는지 체크
        if 'rating' not in data :
            return { 'message' : '필수값이 없습니다.'}, HTTPStatus.BAD_REQUEST

        # JWT 인증토큰에서 유저아이디 뽑아온다.
        user_id = get_jwt_identity()

        # 3. 데이터베이스 커넥션 연결
        connection = get_mysql_connection()

        # 4. 커서 가져오기
        cursor = connection.cursor(dictionary=True)

        # 5. 쿼리문 만들기
        query = """insert into rating(rating, item_id, user_id)
                    values (%s, %s, %s);"""
        

        param = (data['rating'], data['item_id'], user_id)

        # 6. 쿼리문 실행
        c_result = cursor.execute(query,param)
        print(c_result)

        connection.commit()

        # 7. 커서와 커넥션 닫기
        cursor.close()
        connection.close()

        # 8. 클라이언트에 response 하기
        return {'err_code':0 }, HTTPStatus.OK

class MovieRecommandResource(Resource) :    
    # 내 정보에 있는 리뷰 정보와 movie_correlations를 통해서 
    # 가중치가 높은 10개의 영화를 추천해 주는 함수
    @jwt_required()
    def get(self, user_id) :
        data = request.get_json()

        token_user_id = get_jwt_identity()

        if token_user_id != user_id :
            return {'err_code' : 1}, HTTPStatus.UNAUTHORIZED


        connection = get_mysql_connection()

        cursor = connection.cursor(dictionary=True)

        query = """select m.title, r.rating
                    from rating r
                    join movie m on m.id = r.item_id
                    join movie_user u on u.id = r.user_id
                    where u.id = %s;"""
        
        param = (user_id, )

        cursor.execute(query,param)
        records = cursor.fetchall()

        records = DataFrame(records, columns=['title','rating'])
        print(records)

        movie_correlations = pd.read_csv('movie_correlations.csv')

        myRatings = records
        similar_movies_list = pd.DataFrame()
        for i in np.arange(0, len(myRatings)):
            movie_title = myRatings['title'][i]
            similar_movie = movie_correlations[myRatings['title'][i]].dropna().sort_values(ascending=False).to_frame()
            similar_movie.columns = ['Correlation']
            similar_movie['Weight'] = similar_movie['Correlation'] * myRatings['rating'][i]
            similar_movies_list = similar_movies_list.append(similar_movie)
        result = similar_movies_list.sort_values('Weight', ascending=False).head(10)
        result = result['Weight']
        # print(result)
        index = result.index.values
        # print(index[1])

        query = """select title from movie
                    where id = %s or id = %s or id = %s or id = %s or id = %s or id = %s or id = %s or id = %s or id = %s or id = %s;"""

        param = []
        for i in np.arange(0, len(index)):
            # print(index[i])
            param.append(index[i])
        
        param = [int (i) for i in param]

        # print(param)
        param = tuple(param)
        cursor.execute(query,param)
        records = cursor.fetchall()
        
        # print(result)
        result = result.to_frame()
        # print(result['Weight'])
        index = []
        for i in np.arange(0, len(records)) :
            prob = records[i]['title']
            index.append(prob)

        ret = result.reindex()
        ret['Movie'] = index
        ret = ret[['Movie', 'Weight']]
        # print(ret)


        # 7. 커서와 커넥션 닫기
        ret = ret.to_json(orient='records')

        cursor.close()
        connection.close()

        # 8. 클라이언트에 response 하기
        return {'recommand': ret}, HTTPStatus.OK


                    




