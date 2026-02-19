# 🚀 StartLine Dev 개발 환경 설정 가이드

## 필수 사항

- **Python 3.13+**
- **PostgreSQL 14+**
- **Git**

---

## 📋 팀원 설정 방법 (모두 동일)

### 1️⃣ 프로젝트 클론

```bash
git clone <repository-url>
cd StartLineDev
```

### 2️⃣ 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate  # Windows
```

### 3️⃣ 패키지 설치

```bash
pip install -r requirements.txt
```

### 4️⃣ PostgreSQL 설정

#### 4-1. PostgreSQL 설치 (처음 한 번만)

**macOS:**
```bash
# Homebrew로 설치
brew install postgresql

# 서비스 시작
brew services start postgresql
```

**Windows:**
- [PostgreSQL 공식 설치프로그램](https://www.postgresql.org/download/windows/) 다운로드 및 설치

**Linux (Ubuntu):**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo service postgresql start
```

#### 4-2. 데이터베이스 생성

```bash
# PostgreSQL 접속 (자신의 PostgreSQL 사용자명으로)
# macOS 사용자 예시:
psql -U $(whoami)

# Windows 사용자 예시:
psql -U postgres

# 데이터베이스 생성 (모두 동일)
CREATE DATABASE startlinedev;

# 확인
\l

# 나가기
\q
```

**⚠️ 중요: 각 팀원이 자신의 PostgreSQL 사용자명을 사용해야 합니다.**
- macOS: 기본값은 설치된 맥 사용자명 (예: `isujong`, `john` 등)
- Windows: 기본값은 `postgres` (설치 중 설정한 비밀번호 필요)
- Linux: 기본값은 `postgres`

### 5️⃣ 환경변수 설정

```bash
# .env 파일 생성 (프로젝트 루트)
cp .env.example .env
```

`.env` 파일 수정 (각 팀원이 자신의 정보로 수정):
```env
# 각자 자신의 PostgreSQL 사용자명 입력
DB_ENGINE=django.db.backends.postgresql
DB_NAME=startlinedev          # 모두 동일
DB_USER=your_postgres_user    # 자신의 PostgreSQL 사용자명으로 변경
DB_PASSWORD=your_password     # 자신의 PostgreSQL 비밀번호
DB_HOST=localhost
DB_PORT=5432

SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

**예시:**
- macOS 사용자 (isujong): `DB_USER=isujong`
- Windows 사용자: `DB_USER=postgres`

### 6️⃣ 마이그레이션 및 초기 데이터

```bash
# 마이그레이션 적용
python manage.py migrate

# 관리자 계정 생성 (처음 한 번만)
python manage.py createsuperuser
```

### 7️⃣ 서버 실행

```bash
python manage.py runserver
```

브라우저에서 확인:
- 메인 페이지: `http://localhost:8000`
- 관리자 페이지: `http://localhost:8000/admin`

---

## 🗄️ 데이터베이스 확인
# 자신의 PostgreSQL 사용자명으로 접속
psql -d startlinedev -U your_postgres_user
### Django Admin (추천)
```
http://localhost:8000/admin
```

### PostgreSQL 커맨드라인
```bash
psql -d startlinedev -U isujong

# 테이블 목록
\dt

# 특정 테이블 조회
SELECT * FROM accounts_user;
SELECT * FROM learning_learningresource;

# 나가기
\q
```

### Django Shell
```bash
python manage.py shell

from accounts.models import User
User.objects.all()
```

---

## 📦 필수 패키지 목록

현재 `requirements.txt`에 포함된 패키지:

```
Django==5.2.10          # Django 프레임워크
django-allauth==65.14.0 # 사용자 인증
psycopg2-binary==2.9.10 # PostgreSQL 드라이버
pillow==12.1.0          # 이미지 처리
```

---

## ⚠️ 일반적인 문제 해결

### "role 'isujong' does not exist"
```bash
# 현재 사용자 확인
whoami

# PostgreSQL 사용자 생성 (필요시)
createuser -s isujong
```

### "database 'startlinedev' does not exist"
```bash
# 데이터베이스 생성
createdb startlinedev
```

### psycopg2 설치 오류 (macOS)
```bash
pip install psycopg2-binary
# 또는
pip install --no-binary :all: psycopg2
```

### 마이그레이션 충돌
```bash
# 마이그레이션 상태 확인
python manage.py showmigrations

# 특정 마이그레이션 제거 (필요시)
python manage.py migrate <app> <migration_number>
```

---

## 🔐 보안 주의사항

⚠️ **절대 커밋하지 말기:**
- `.env` 파일 (`.gitignore`에 포함)
- `db.sqlite3`
- `local_settings.py`
- `venv/` 디렉토리

✅ **공유할 파일:**
- `requirements.txt` (패키지 목록)
- `.env.example` (샘플 설정)
- `SETUP_GUIDE.md` (이 파일)

---

## 🤝 협업 가이드

### 새로운 패키지 추가 시
```bash
pip install <package-name>
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add: <package-name>"
```

### 마이그레이션 생성 시
```bash
python manage.py makemigrations
python manage.py migrate

# 커밋
git add <app>/migrations/<new_migration_file>
git commit -m "Migration: <description>"
```

### Pull 받은 후
```bash
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

---

## 📞 문제 발생 시

문제 발생 시 다음 정보를 함께 공유해주세요:
- OS 및 Python 버전: `python --version`
- PostgreSQL 버전: `psql --version`
- 전체 에러 메시지
- 수행한 명령어
