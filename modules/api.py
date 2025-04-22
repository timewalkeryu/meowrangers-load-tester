"""
모듈 설명: API 호출 관련 함수
"""
import time
import json
import uuid
import asyncio
from datetime import datetime

from . import config
from . import utils

async def call_api(session, url, method, headers=None, payload=None, api_name=None, index=None):
    """일반적인 API 호출 함수 - HTTP 상태 코드 200을 성공 기준으로 사용"""
    # 루프별 세마포어 관리를 위한 딕셔너리 (함수 외부에 선언)
    if not hasattr(call_api, '_semaphores'):
        call_api._semaphores = {}

    # 현재 이벤트 루프 가져오기
    current_loop = asyncio.get_running_loop()
    loop_id = id(current_loop)

    # 현재 루프에 대한 세마포어가 없으면 생성
    if loop_id not in call_api._semaphores:
        call_api._semaphores[loop_id] = asyncio.Semaphore(300)

    async with call_api._semaphores[loop_id]:
        start_time = time.time()
        api_name = api_name or url.split('/')[-1]  # URL의 마지막 부분을 API 이름으로 사용

        if method.upper() not in ["GET", "POST", "PUT", "DELETE"]:
            print(f"지원하지 않는 HTTP 메서드: {method}")
            return None, False  # 결과와 성공 여부를 함께 반환

        error_msg = None
        result = None
        status_code = None
        elapsed = 0
        is_success = False  # API 호출 최종 성공 여부

        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    elapsed = time.time() - start_time
                    utils.api_times[api_name].append(elapsed)
                    status_code = response.status

                    # 성공 기준: HTTP 상태 코드 200
                    is_success = (response.status == 200)

                    try:
                        result = await response.json()
                        if is_success:
                            print(f"[{index}] {api_name} 완료: {elapsed:.2f}초")
                        else:
                            print(f"[{index}] {api_name} 실패: HTTP {response.status}")
                    except:
                        try:
                            result = await response.text()
                        except:
                            result = None
                        if not is_success:
                            print(f"[{index}] {api_name} 실패: HTTP {response.status} (응답 처리 오류)")
            else:  # POST, PUT, DELETE
                request_kwargs = {"headers": headers}
                if payload:
                    request_kwargs["json"] = payload

                request_method = getattr(session, method.lower())
                async with request_method(url, **request_kwargs) as response:
                    elapsed = time.time() - start_time
                    utils.api_times[api_name].append(elapsed)
                    status_code = response.status

                    # 성공 기준: HTTP 상태 코드 200
                    is_success = (response.status == 200)

                    try:
                        result = await response.json()
                        if is_success:
                            print(f"[{index}] {api_name} 완료: {elapsed:.2f}초")
                        else:
                            print(f"[{index}] {api_name} 실패: HTTP {response.status}")
                    except:
                        try:
                            result = await response.text()
                        except:
                            result = None
                        if not is_success:
                            print(f"[{index}] {api_name} 실패: HTTP {response.status} (응답 처리 오류)")

        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            print(f"[{index}] {api_name} 중 오류: {str(e)} ({elapsed:.2f}초)")
            is_success = False  # 예외 발생 시 항상 실패로 처리

        # 실패한 경우에만 오류 기록
        if not is_success:
            utils.errors.append(f"{api_name}-{index}: {error_msg or f'HTTP {status_code}'}")

        # 상세 로그 기록 - 성공 여부에 따라 error 필드를 다르게 설정
        utils.log_detailed_request(
            user_id=index,
            api_name=api_name,
            url=url,
            method=method,
            headers=headers,
            payload=payload,
            response=result,
            status_code=status_code,
            elapsed_time=elapsed,
            error=None if is_success else (error_msg or f'HTTP {status_code}'),  # 성공 시 오류 없음
            is_success=is_success  # 명시적으로 성공 여부 저장
        )

        # 결과와 성공 여부를 함께 반환
        return result, is_success

async def create_token(session, index):
    """토큰 생성 함수"""
    url = f"{config.BASE_URL}/api/create-token"

    payload = {
        "platform": config.PLATFORM_TYPE,
        "server_alias": config.SERVER_ALIAS
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    result, is_success = await call_api(
        session=session,
        url=url,
        method="POST",
        payload=payload,
        api_name="CreateToken",
        index=index
    )

    # 성공하지 않았다면 None 반환
    if not is_success or not result:
        return None

    # 토큰 추출
    token = None
    try:
        if "Result" in result and isinstance(result["Result"], dict) and "token" in result["Result"]:
            token = result["Result"]["token"]
        elif "result" in result and isinstance(result["result"], dict) and "token" in result["result"]:
            token = result["result"]["token"]
        elif "token" in result:
            token = result["token"]
    except Exception as e:
        print(f"[{index}] 토큰 추출 중 오류: {str(e)}")
        utils.errors.append(f"CreateToken-{index}: 토큰 추출 오류 - {str(e)}")
        return None

    if not token:
        print(f"[{index}] 응답에서 토큰을 찾을 수 없음: {result}")
        utils.errors.append(f"CreateToken-{index}: 토큰 없음")
        return None

    return token

async def connect_provider(session, index, token):
    """게스트 계정 연결 함수"""
    url = f"{config.BASE_URL}/api/connect-provider"

    # 랜덤 UUID 생성
    account_key = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "using_account_key": account_key,
        "forget_account_key": "",
        "data_source": "DEVICE",
        "provider_type": "GUEST"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    result, is_success = await call_api(
        session=session,
        url=url,
        method="POST",
        headers=headers,
        payload=payload,
        api_name="ConnectProvider",
        index=index
    )

    # 성공하지 않았다면 None 반환
    if not is_success or not result:
        return None

    # 새 토큰 추출
    new_token = None
    try:
        if "Result" in result and isinstance(result["Result"], dict) and "token" in result["Result"]:
            new_token = result["Result"]["token"]
        elif "result" in result and isinstance(result["result"], dict) and "token" in result["result"]:
            new_token = result["result"]["token"]
        elif "token" in result:
            new_token = result["token"]
    except Exception as e:
        print(f"[{index}] 새 토큰 추출 중 오류: {str(e)}")
        utils.errors.append(f"ConnectProvider-{index}: 새 토큰 추출 오류 - {str(e)}")
        return None

    if not new_token:
        print(f"[{index}] ConnectProvider 응답에서 새 토큰을 찾을 수 없음")
        utils.errors.append(f"ConnectProvider-{index}: 새 토큰 없음")
        return None

    return new_token

async def check_app_version(session, index, token):
    """앱 버전 확인 함수"""
    url = f"{config.BASE_URL}/api/app-versions?app_version={config.APP_VERSION}&platform={config.PLATFORM_TYPE}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="CheckAppVersion",
        index=index
    )

    return is_success

async def get_timestamp(session, index, token):
    """서버 타임스탬프 조회 함수"""
    url = f"{config.BASE_URL}/api/timestamp"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetTimestamp",
        index=index
    )

    return is_success

async def set_user_data(session, index, token):
    """사용자 데이터 설정 함수"""
    url = f"{config.BASE_URL}/api/user-data"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # 유저 데이터 로드
    user_data = utils.load_user_data()

    # 현재 타임스탬프로 마지막 로그인 시간 업데이트
    user_data["last_login"] = datetime.now().isoformat()

    payload = {
        "data": json.dumps(user_data),  # 문자열로 직렬화
        "force_update": 0
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="POST",
        headers=headers,
        payload=payload,
        api_name="SetUserData",
        index=index
    )

    return is_success

async def get_user_data(session, index, token):
    """사용자 데이터 요청 함수"""
    url = f"{config.BASE_URL}/api/user-data"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetUserData",
        index=index
    )

    return is_success

async def get_all_mails(session, index, token):
    """모든 메일 조회 함수"""
    url = f"{config.BASE_URL}/api/received-mails"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetAllMails",
        index=index
    )

    return is_success

async def get_unclaimed_mail_count(session, index, token):
    """읽지 않은 메일 수 조회 함수"""
    url = f"{config.BASE_URL}/api/received-mail-count"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetUnclaimedMailCount",
        index=index
    )

    return is_success

async def get_season_pass_info(session, index, token):
    """시즌 패스 정보 조회 함수"""
    url = f"{config.BASE_URL}/api/game-events?event_type=SEASON_PASS"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetSeasonPassInfo",
        index=index
    )

    return is_success

async def get_event_info(session, index, token):
    """이벤트 정보 조회 함수"""
    url = f"{config.BASE_URL}/api/game-events?event_type=EVENT"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetEventInfo",
        index=index
    )

    return is_success

async def get_announcement(session, index, token):
    """공지사항 조회 함수"""
    url = f"{config.BASE_URL}/api/announcements"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetAnnouncement",
        index=index
    )

    return is_success

async def get_rolling_announcement(session, index, token):
    """롤링 공지사항 조회 함수"""
    url = f"{config.BASE_URL}/api/rolling-announcements"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # call_api 함수는 이제 (result, is_success)를 반환
    _, is_success = await call_api(
        session=session,
        url=url,
        method="GET",
        headers=headers,
        api_name="GetRollingAnnouncement",
        index=index
    )

    return is_success