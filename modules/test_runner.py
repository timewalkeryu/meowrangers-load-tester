"""
모듈 설명: 테스트 실행 및 관리 기능
"""
import asyncio
import aiohttp
import time

from . import config
from . import api
from . import utils

async def create_token_and_connect_for_user(session, index, semaphore):
    """단일 사용자에 대한 토큰 생성 및 연결 프로세스"""
    # 세마포어를 사용하여 동시 요청 수 제한
    async with semaphore:
        print(f"사용자 {index}: 인증 프로세스 시작")

        # 1. CreateToken 호출
        initial_token = await api.create_token(session, index)
        if not initial_token:
            print(f"사용자 {index}: 초기 토큰 생성 실패")
            return None

        # 약간의 지연 추가 (선택사항)
        await asyncio.sleep(0.1)

        # 2. ConnectProvider 호출하여 새 토큰 획득
        new_token = await api.connect_provider(session, index, initial_token)
        if not new_token:
            print(f"사용자 {index}: ConnectProvider 실패")
            return None

        print(f"사용자 {index}: 인증 프로세스 완료, 새 토큰 획득")
        return index, new_token

async def create_tokens_and_connect_parallel(concurrent_users, max_concurrent_auth=5):
    """병렬로 토큰 생성 및 인증 프로세스 수행 (제한된 동시성으로)"""
    new_tokens = []

    print(f"{concurrent_users}명의 사용자에 대해 제한된 동시성({max_concurrent_auth})으로 인증 프로세스를 진행합니다...")

    # 세마포어를 사용하여 동시 인증 요청 수 제한
    semaphore = asyncio.Semaphore(max_concurrent_auth)

    # HTTP 클라이언트 세션 생성
    timeout = aiohttp.ClientTimeout(total=60)  # 타임아웃 설정 (60초)
    connector = aiohttp.TCPConnector(ssl=False)  # SSL 검증 비활성화

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 모든 사용자에 대한 인증 태스크 생성
        tasks = [create_token_and_connect_for_user(session, i, semaphore) for i in range(concurrent_users)]

        # 모든 태스크 실행 및 결과 수집
        results = await asyncio.gather(*tasks)

        # None이 아닌 결과만 필터링하여 토큰 배열 생성
        new_tokens = [result for result in results if result is not None]

    print(f"인증 프로세스 완료: {len(new_tokens)}/{concurrent_users} 사용자 성공")
    return new_tokens

async def run_api_tests(session, index, token):
    """한 사용자에 대해 모든 API 테스트 실행"""
    print(f"사용자 {index}: API 테스트 시작")

    # 1. SetUserData 호출
    set_data_result = await api.set_user_data(session, index, token)
    if not set_data_result:
        print(f"사용자 {index}: SetUserData 실패로 테스트 중단")
        return False

    # 2. GetUserData 호출
    get_data_result = await api.get_user_data(session, index, token)
    if not get_data_result:
        print(f"사용자 {index}: GetUserData 실패")

    # 3. GetAllMails 호출
    mail_result = await api.get_all_mails(session, index, token)
    if not mail_result:
        print(f"사용자 {index}: GetAllMails 실패")

    # 4. GetSeasonPassInfo 호출
    season_result = await api.get_season_pass_info(session, index, token)
    if not season_result:
        print(f"사용자 {index}: GetSeasonPassInfo 실패")

    # 5. GetEventInfo 호출
    event_result = await api.get_event_info(session, index, token)
    if not event_result:
        print(f"사용자 {index}: GetEventInfo 실패")

    # 6. GetAnnouncement 호출
    announcement_result = await api.get_announcement(session, index, token)
    if not announcement_result:
        print(f"사용자 {index}: GetAnnouncement 실패")

    # 7. GetRollingAnnouncement 호출
    rolling_result = await api.get_rolling_announcement(session, index, token)
    if not rolling_result:
        print(f"사용자 {index}: GetRollingAnnouncement 실패")

    print(f"사용자 {index}: API 테스트 완료")
    return True

async def run_load_test(concurrent_users):
    """전체 부하 테스트 실행"""
    # 최대 동시 인증 프로세스 설정 (서버 부하 및 속도 제한 고려)
    max_concurrent_auth = min(config.MAX_CONCURRENT_AUTH, concurrent_users)

    # 1. 제한된 동시성으로 토큰 생성 및 ConnectProvider 호출
    start_time = time.time()
    tokens = await create_tokens_and_connect_parallel(concurrent_users, max_concurrent_auth)
    auth_time = time.time() - start_time

    if not tokens:
        print("인증된 토큰이 없어 테스트를 중단합니다.")
        return

    print(f"\n인증 프로세스 총 소요 시간: {auth_time:.2f}초")
    print(f"{len(tokens)}개의 인증된 토큰으로 API 테스트를 시작합니다...")

    # 2. 생성된 새 토큰으로 API 테스트
    timeout = aiohttp.ClientTimeout(total=30)  # 타임아웃 설정 (30초)
    connector = aiohttp.TCPConnector(limit=0, ssl=False)  # 동시 연결 제한 없음

    start_time = time.time()
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 모든 사용자에 대해 API 테스트 태스크 생성 및 실행
        tasks = [run_api_tests(session, index, token) for index, token in tokens]
        results = await asyncio.gather(*tasks)

    api_test_time = time.time() - start_time
    successful_tests = sum(1 for result in results if result)
    print(f"\nAPI 테스트 총 소요 시간: {api_test_time:.2f}초")
    print(f"성공적으로 완료된 API 테스트: {successful_tests}/{len(tokens)}")