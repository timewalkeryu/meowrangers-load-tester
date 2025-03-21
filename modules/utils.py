"""
모듈 설명: 유틸리티 함수 모음
"""
import os
import json
from datetime import datetime
from collections import defaultdict

from . import config

# 결과 저장용 변수
api_times = defaultdict(list)  # 각 API별 응답 시간 저장
set_execution_times = []  # 각 세트별 전체 실행 시간 저장
errors = []  # 오류 저장
detailed_logs = []  # 상세 로그 저장

def ensure_directory_exists(directory):
    """지정된 디렉터리가 존재하는지 확인하고, 없으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"디렉터리 생성: {directory}")

def load_user_data():
    """fixture/data.json 파일에서 유저 데이터 로드"""
    ensure_directory_exists(config.FIXTURE_DIR)
    data_file = os.path.join(config.FIXTURE_DIR, "data.json")

    if not os.path.exists(data_file):
        # 파일이 없으면 기본 데이터로 생성
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(config.DEFAULT_USER_DATA, f, ensure_ascii=False, indent=2)
        print(f"기본 유저 데이터 파일 생성: {data_file}")
        return config.DEFAULT_USER_DATA

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"유저 데이터 파일 로드 중 오류: {str(e)}")
        print("기본 유저 데이터를 사용합니다.")
        return config.DEFAULT_USER_DATA

def mask_token(token):
    """토큰을 마스킹하여 보안 강화"""
    if not token:
        return ""

    if len(token) > 10:
        return token[:5] + '*' * (len(token) - 10) + token[-5:]
    return token

def log_detailed_request(user_id, api_name, url, method, headers, payload, response, status_code, elapsed_time, error=None, is_success=None):
    """요청과 응답 정보를 상세하게 기록"""
    try:
        # 헤더에서 토큰 마스킹 처리
        masked_headers = None
        if headers:
            masked_headers = dict(headers)  # 새 사전으로 복사
            if 'Authorization' in masked_headers and masked_headers['Authorization']:
                auth_value = masked_headers['Authorization']
                if auth_value.startswith('Bearer '):
                    token = auth_value[7:]  # 'Bearer ' 이후의 토큰 부분
                    masked_token = mask_token(token)
                    masked_headers['Authorization'] = f'Bearer {masked_token}'

        # is_success가 명시적으로 지정되지 않은 경우, error의 존재 여부로 판단
        if is_success is None:
            is_success = error is None

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "api_name": api_name,
            "url": url,
            "method": method,
            "headers": masked_headers,
            "status_code": status_code,
            "elapsed_time": elapsed_time,
            "error": error,  # 성공 시 None, 실패 시 오류 메시지
            "is_success": is_success  # 명시적 성공 여부 표시
        }

        # 요청 페이로드 추가 (있는 경우)
        if payload is not None:
            # 민감한 정보가 있으면 마스킹
            if isinstance(payload, dict):
                filtered_payload = dict(payload)
                # using_account_key가 있는 경우 (계정 정보)
                if "using_account_key" in filtered_payload:
                    filtered_payload["using_account_key"] = mask_token(filtered_payload["using_account_key"])
                log_entry["payload"] = filtered_payload
            else:
                log_entry["payload"] = payload

        # 응답 데이터가 너무 크면 요약 정보만 저장
        if response:
            try:
                # 민감한 정보 필터링 (토큰 등)
                if isinstance(response, dict):
                    filtered_response = dict(response)  # 새 사전으로 복사

                    # Result 안에 token이 있는 경우 (대문자)
                    if "Result" in filtered_response and isinstance(filtered_response["Result"], dict):
                        result_dict = dict(filtered_response["Result"])
                        if "token" in result_dict:
                            result_dict["token"] = mask_token(result_dict["token"])
                        if "uid" in result_dict:
                            result_dict["uid"] = mask_token(result_dict["uid"])
                        filtered_response["Result"] = result_dict

                    # result 안에 token이 있는 경우 (소문자)
                    elif "result" in filtered_response and isinstance(filtered_response["result"], dict):
                        result_dict = dict(filtered_response["result"])
                        if "token" in result_dict:
                            result_dict["token"] = mask_token(result_dict["token"])
                        if "uid" in result_dict:
                            result_dict["uid"] = mask_token(result_dict["uid"])
                        filtered_response["result"] = result_dict

                    # 최상위에 token이 있는 경우
                    elif "token" in filtered_response:
                        filtered_response["token"] = mask_token(filtered_response["token"])

                    # 유저 데이터가 있는 경우 (너무 크면 요약만)
                    if ("data" in filtered_response and isinstance(filtered_response["data"], str) and
                            len(filtered_response["data"]) > 1000):
                        filtered_response["data"] = f"[대용량 데이터 - {len(filtered_response['data'])} 바이트]"

                    if ("Result" in filtered_response and "data" in filtered_response["Result"] and
                            isinstance(filtered_response["Result"]["data"], str) and
                            len(filtered_response["Result"]["data"]) > 1000):
                        filtered_response["Result"]["data"] = f"[대용량 데이터 - {len(filtered_response['Result']['data'])} 바이트]"

                    log_entry["response"] = filtered_response
                else:
                    # 응답이 딕셔너리가 아닌 경우, 문자열로 변환하여 요약 저장
                    response_str = str(response)
                    if len(response_str) > 500:
                        log_entry["response"] = f"[대용량 응답 - {len(response_str)} 바이트]"
                    else:
                        log_entry["response"] = response_str
            except Exception as e:
                log_entry["response"] = f"[응답 처리 오류: {str(e)}]"

        detailed_logs.append(log_entry)
    except Exception as e:
        print(f"로그 기록 중 오류 발생: {str(e)}")
        # 오류가 발생해도 테스트를 중단하지 않음