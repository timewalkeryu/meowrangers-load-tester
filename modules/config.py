"""
모듈 설명: 설정 및 상수 정의
"""
import os

# 서버 설정
BASE_URL = "https://meowrangers-dev.layerlabgames.com"  # 개발 환경 URL
# BASE_URL = "https://meowrangers-qa.layerlabgames.com"  # QA 환경 URL
# BASE_URL = "https://meowrangers-prod.layerlabgames.com"  # 프로덕션 환경 URL

# 테스트 설정
SERVER_ALIAS = "SEOUL-001"
PLATFORM_TYPE = "DEVICE"
DEFAULT_CONCURRENT_USERS = 10  # 기본 동시 사용자 수
DEFAULT_TEST_SETS = 2          # 기본 API 테스트 세트 수
MAX_CONCURRENT_AUTH = 10  # 최대 동시 인증 프로세스 수

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