# MySQL 접속 정보를, 딕셔너리 형태로 저장한다.
db_config = {
    'host' : 'database-1.cdxb0pb9vr70.us-east-2.rds.amazonaws.com',
    'database' : 'yhdb',
    'user' : 'streamlit',
    'password' : '1q2w3e4r5t'
}

# 클래스란 ? 속성과 함수로 구성된 것.
# 클래스를 만드는 이유? 물건을 있는 그대로 바라보는 관점.

# 개
# 개의 속성 : 눈, 코, 입, 귀, 다리, 꼬리
# 개의 함수(행동) : 짖는다. 문다. 꼬리친다.

# 책상
# 책상의 속성 : 재질, 다리, 다리갯수, 판 모양
# 책상 함수(행동) : 옮긴다. 물건을 올려놓는다.

# 플라스크 앱의 설정용 클래스.

class Config :
    DEBUG = True

    # JWT용 시크릿 키
    SECRET_KEY = 'leejaechang_06_11'

# 비밀번호 암호화를 위한 salt 설정 => 해킹방지를 위해서
salt = 'hello_test'

