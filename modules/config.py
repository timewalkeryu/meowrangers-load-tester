"""
모듈 설명: 설정 및 상수 정의
"""
import os

# 서버 설정
# BASE_URL = "https://meowrangers-dev.layerlabgames.com"  # 개발 환경 URL
# BASE_URL = "https://meowrangers-qa.layerlabgames.com"  # QA 환경 URL
# BASE_URL = "https://meowrangers-prod.layerlabgames.com"  # 프로덕션 환경 URL

# 서버 설정 (기본값은 개발 환경)
# 환경 변수나 커맨드라인 인자로 덮어쓸 수 있음
SERVER_ENVIRONMENTS = {
    "dev": "https://meowrangers-dev.layerlabgames.com",
    "qa": "https://meowrangers-qa.layerlabgames.com",
    "live": "https://meowrangers-prod.layerlabgames.com"
}

# 기본값은 개발 환경
BASE_URL = SERVER_ENVIRONMENTS.get("dev")

# HTTP 클라이언트 설정
HTTP_TIMEOUT = 60  # 타임아웃 설정 (초)
HTTP_MAX_CONNECTIONS = 2000  # 최대 동시 연결 수
HTTP_VERIFY_SSL = False  # SSL 검증 여부

# API 호출 제한 설정
API_SEMAPHORE_LIMIT = 2000  # API 호출에 사용할 세마포어 제한

# 테스트 설정
SERVER_ALIAS = "SEOUL-001"
PLATFORM_TYPE = "DEVICE"
APP_VERSION = "1.0.0"  # 앱 버전 설정
DEFAULT_CONCURRENT_USERS = 1000  # 기본 동시 사용자 수 및 최대 동시 인증 프로세스 수
DEFAULT_TEST_SETS = 1          # 기본 API 테스트 세트 수

# 테스트 결과 검증 설정
ERROR_THRESHOLD = 0.0         # 허용 최대 오류율(%)
MIN_SUCCESS_RATE = 100.0      # 필요한 최소 성공률(%)

# 디렉터리 설정
LOG_DIR = "log"
FIXTURE_DIR = "fixture"

# 기본 유저 데이터 템플릿
DEFAULT_USER_DATA = {
    "level": 1,
    "exp": 0,
    "gold": 10000,
    "gem": 1000,
    "energy": 100,
    "max_energy": 100,
    "last_login": "",
    "inventory": {
        "items": [],
        "characters": [
            {"id": "char_001", "level": 1, "exp": 0, "equipped": True}
        ]
    },
    "settings": {
        "sound": True,
        "music": True,
        "vibration": True,
        "notification": True
    },
    "tutorial_completed": False
}