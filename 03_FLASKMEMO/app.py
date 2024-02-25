from flask import Flask, render_template, request, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
    
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 로그인 페이지의 뷰 함수 이름

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://funcoding:funcoding@localhost/my_memo_app'
# SQLAlchemy의 수정 추적 기능을 비활성화합니다. (성능상의 이유로 권장됩니다.)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 세션 및 쿠키에 대한 보안 향상을 위해 필요한 비밀 키를 설정합니다.
app.config['SECRET_KEY'] = 'mysecretkey'
db = SQLAlchemy(app)

# 데이터 모델 정의
class Memo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 사용자 참조 추가
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)

    def __repr__(self):
        return f'<Memo {self.title}>'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(512))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# 기존 라우트
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return '이것은 마이 메모 앱의 소개 페이지입니다.'

# 데이터베이스 생성
with app.app_context():
    db.create_all()

@app.route('/memos/create', methods=['POST'])
@login_required
def create_memo():
    title = request.json['title']
    content = request.json['content']
    new_memo = Memo(user_id=current_user.id, title=title, content=content)  # 현재 로그인한 사용자의 ID 추가
    db.session.add(new_memo)
    db.session.commit()
    return jsonify({'message': 'Memo created'}), 201

# 메모 조회
@app.route('/memos', methods=['GET'])
@login_required
def list_memos():
    memos = Memo.query.filter_by(user_id=current_user.id).all()  # 현재 로그인한 사용자의 메모만 조회
    return render_template('memos.html', memos=memos, username=current_user.username)  # 사용자별 메모를 표시하는 템플릿 렌더링


# 메모 업데이트
@app.route('/memos/update/<int:id>', methods=['PUT'])
@login_required
def update_memo(id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()  # 현재 사용자의 메모만 선택
    if memo:
        memo.title = request.json['title']
        memo.content = request.json['content']
        db.session.commit()
        return jsonify({'message': 'Memo updated'}), 200
    else:
        abort(404, description="Memo not found or not authorized")

# 메모 삭제
@app.route('/memos/delete/<int:id>', methods=['DELETE'])
@login_required
def delete_memo(id):
    memo = Memo.query.filter_by(id=id, user_id=current_user.id).first()  # 현재 사용자의 메모만 선택
    if memo:
        db.session.delete(memo)
        db.session.commit()
        return jsonify({'message': 'Memo deleted'}), 200
    else:
        abort(404, description="Memo not found or not authorized")
        

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return jsonify({'message': 'Logged in successfully'}), 200
        return abort(401, description="Invalid credentials")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'Account created successfully'}), 201
    return render_template('signup.html')