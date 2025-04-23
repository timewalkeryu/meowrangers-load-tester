"""
모듈 설명: 테스트 실행 및 관리 기능 (반복 실행 기능 추가)
"""
import asyncio
import aiohttp
import time
import random

from . import config
from . import api
from . import utils


async def create_token_and_connect_for_user(session, index):
    """단일 사용자에 대한 토큰 생성 및 연결 프로세스 (세마포어 제거)"""
    print(f"사용자 {index}: 인증 프로세스 시작")

    # 1. CreateToken 호출
    initial_token = await api.create_token(session, index)
    if not initial_token:
        print(f"사용자 {index}: 초기 토큰 생성 실패")
        return None

    # 약간의 지연 추가 (선택사항)
    # await asyncio.sleep(0.1)

    # 2. ConnectProvider 호출하여 새 토큰 획득
    new_token = await api.connect_provider(session, index, initial_token)
    if not new_token:
        print(f"사용자 {index}: ConnectProvider 실패")
        return None

    print(f"사용자 {index}: 인증 프로세스 완료, 새 토큰 획득")
    return index, new_token


async def create_tokens_and_connect_parallel(concurrent_users):
    """병렬로 토큰 생성 및 인증 프로세스 수행 (동시성 제한 없음)"""
    new_tokens = []

    print(f"{concurrent_users}명의 사용자에 대해 완전 병렬로 인증 프로세스를 진행합니다...")

    # HTTP 클라이언트 세션 생성
    timeout = aiohttp.ClientTimeout(total=config.HTTP_TIMEOUT)  # 타임아웃 설정
    connector = aiohttp.TCPConnector(ssl=config.HTTP_VERIFY_SSL, limit=config.HTTP_MAX_CONNECTIONS)  # SSL 검증 비활성화, 연결 제한 해제

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        # 모든 사용자에 대한 인증 태스크 생성 (세마포어 없음)
        tasks = [create_token_and_connect_for_user(session, i) for i in range(concurrent_users)]

        # 모든 태스크 실행 및 결과 수집
        results = await asyncio.gather(*tasks)

        # None이 아닌 결과만 필터링하여 토큰 배열 생성
        new_tokens = [result for result in results if result is not None]

    print(f"인증 프로세스 완료: {len(new_tokens)}/{concurrent_users} 사용자 성공")
    return new_tokens


async def run_api_test_set(session, index, token, set_id):
    """한 사용자에 대해 하나의 API 테스트 세트 실행"""
    print(f"사용자 {index} - 세트 {set_id}: API 테스트 세트 시작")

    # 세트 시작 시간 기록
    set_start_time = time.time()

    # API 결과 추적
    api_results = {}

    # 1. CheckAppVersion 호출 (추가됨)
    check_app_result = await api.check_app_version(session, index, token)
    api_results["CheckAppVersion"] = check_app_result
    if not check_app_result:
        print(f"사용자 {index} - 세트 {set_id}: CheckAppVersion 실패")

    # 2. GetTimestamp 호출 (추가됨)
    timestamp_result = await api.get_timestamp(session, index, token)
    api_results["GetTimestamp"] = timestamp_result
    if not timestamp_result:
        print(f"사용자 {index} - 세트 {set_id}: GetTimestamp 실패")

    # 3. SetUserData 호출
    set_data_result = await api.set_user_data(session, index, token)
    api_results["SetUserData"] = set_data_result
    if not set_data_result:
        print(f"사용자 {index} - 세트 {set_id}: SetUserData 실패")

    # 4. GetUserData 호출
    get_data_result = await api.get_user_data(session, index, token)
    api_results["GetUserData"] = get_data_result
    if not get_data_result:
        print(f"사용자 {index} - 세트 {set_id}: GetUserData 실패")

    # 5. GetAllMails 호출
    mail_result = await api.get_all_mails(session, index, token)
    api_results["GetAllMails"] = mail_result
    if not mail_result:
        print(f"사용자 {index} - 세트 {set_id}: GetAllMails 실패")

    # 6. GetUnclaimedMailCount 호출 (추가됨)
    mail_count_result = await api.get_unclaimed_mail_count(session, index, token)
    api_results["GetUnclaimedMailCount"] = mail_count_result
    if not mail_count_result:
        print(f"사용자 {index} - 세트 {set_id}: GetUnclaimedMailCount 실패")

    # 7. GetSeasonPassInfo 호출
    season_result = await api.get_season_pass_info(session, index, token)
    api_results["GetSeasonPassInfo"] = season_result
    if not season_result:
        print(f"사용자 {index} - 세트 {set_id}: GetSeasonPassInfo 실패")

    # 8. GetEventInfo 호출
    event_result = await api.get_event_info(session, index, token)
    api_results["GetEventInfo"] = event_result
    if not event_result:
        print(f"사용자 {index} - 세트 {set_id}: GetEventInfo 실패")

    # 9. GetAnnouncement 호출
    announcement_result = await api.get_announcement(session, index, token)
    api_results["GetAnnouncement"] = announcement_result
    if not announcement_result:
        print(f"사용자 {index} - 세트 {set_id}: GetAnnouncement 실패")

    # 10. GetRollingAnnouncement 호출
    rolling_result = await api.get_rolling_announcement(session, index, token)
    api_results["GetRollingAnnouncement"] = rolling_result
    if not rolling_result:
        print(f"사용자 {index} - 세트 {set_id}: GetRollingAnnouncement 실패")

    # 각 테스트 사이에 약간의 지연 추가 (선택 사항)
    # 지연 시간을 줄이려면 이 값을 0.01~0.05 정도로 변경할 수 있습니다
    # await asyncio.sleep(random.uniform(0.01, 0.05))  # 더 짧은 지연으로 변경
    await asyncio.sleep(random.uniform(0.1, 0.5))

    # 세트 종료 시간 기록 및 소요 시간 계산
    set_elapsed_time = time.time() - set_start_time

    # 세트 소요 시간 저장
    utils.set_execution_times.append(set_elapsed_time)

    # API 성공률 계산
    success_count = sum(1 for result in api_results.values() if result)
    api_success_rate = success_count / len(api_results) * 100

    # 세트 성공 여부 판정 - 모든 API가 성공해야 세트가 성공한 것으로 간주
    is_set_success = all(api_results.values())

    print(f"사용자 {index} - 세트 {set_id}: API 테스트 세트 완료 (소요 시간: {set_elapsed_time:.3f}초, 성공률: {api_success_rate:.2f}%, 세트 성공: {'예' if is_set_success else '아니오'})")

    # 세트의 성공 여부와 API 결과를 함께 반환
    return is_set_success, api_results


async def run_repeated_api_tests(token_info, set_count):
    """한 사용자에 대해 API 테스트 세트를 지정된 횟수만큼 반복 실행"""
    index, token = token_info

    # HTTP 클라이언트 세션 생성
    timeout = aiohttp.ClientTimeout(total=config.HTTP_TIMEOUT)  # 타임아웃 설정
    connector = aiohttp.TCPConnector(ssl=config.HTTP_VERIFY_SSL, limit=config.HTTP_MAX_CONNECTIONS)  # SSL 검증 비활성화, 연결 제한 해제

    success_count = 0
    api_success_counts = {}  # 각 API별 성공 횟수 추적

    print(f"사용자 {index}: {set_count}개의 API 테스트 세트 실행 시작")

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = []
        for set_id in range(set_count):
            # 직접 태스크 생성 (세마포어 없음)
            tasks.append(
                asyncio.create_task(
                    run_api_test_set(session, index, token, set_id)
                )
            )

        # 모든 세트의 결과 수집 (각 세트당 성공 여부와 API별 결과 딕셔너리)
        results = await asyncio.gather(*tasks)

        # 세트별 성공 여부 카운트
        success_count = sum(1 for result, _ in results if result)

        # API별 성공률 집계
        for _, api_results in results:
            for api_name, success in api_results.items():
                if api_name not in api_success_counts:
                    api_success_counts[api_name] = {"success": 0, "total": 0}
                api_success_counts[api_name]["total"] += 1
                if success:
                    api_success_counts[api_name]["success"] += 1

    # API별 성공률 출력
    for api_name, counts in api_success_counts.items():
        if counts["total"] > 0:
            success_rate = (counts["success"] / counts["total"]) * 100
            print(f"사용자 {index}: {api_name} API 성공률: {success_rate:.2f}% ({counts['success']}/{counts['total']})")

    print(f"사용자 {index}: {success_count}/{set_count} API 테스트 세트 성공")
    return {
        "set_success_count": success_count,
        "total_sets": set_count,
        "api_success_counts": api_success_counts
    }


async def run_load_test(concurrent_users, set_count=1):
    """전체 부하 테스트 실행"""
    # 1. 무제한 동시성으로 토큰 생성 및 ConnectProvider 호출
    start_time = time.time()
    tokens = await create_tokens_and_connect_parallel(concurrent_users)
    auth_time = time.time() - start_time

    # 인증 성공률 계산
    auth_success_count = len(tokens)
    auth_success_rate = (auth_success_count / concurrent_users) * 100 if concurrent_users > 0 else 0

    if not tokens:
        print("인증된 토큰이 없어 테스트를 중단합니다.")
        return {
            'auth_success_count': auth_success_count,
            'auth_total_count': concurrent_users,
            'auth_success_rate': auth_success_rate,
            'api_set_success_count': 0,
            'api_set_total_count': 0,
            'api_set_success_rate': 0,
            'api_success_rates': {},
            'concurrent_users': concurrent_users,
            'set_count': set_count
        }

    print(f"\n인증 프로세스 총 소요 시간: {auth_time:.2f}초")
    print(f"{len(tokens)}개의 인증된 토큰으로 API 테스트를 시작합니다...")
    print(f"각 사용자별로 {set_count}개의 API 테스트 세트를 실행합니다.")

    # 2. 각 토큰에 대해 지정된 횟수만큼 API 테스트 세트 실행
    start_time = time.time()

    # 모든 사용자에 대해 반복 테스트 태스크 생성 및 실행
    tasks = [run_repeated_api_tests(token_info, set_count) for token_info in tokens]
    results = await asyncio.gather(*tasks)

    api_test_time = time.time() - start_time

    # 세트 성공 계산
    set_success_count = sum(result["set_success_count"] for result in results)
    total_sets = sum(result["total_sets"] for result in results)

    # API별 성공률 집계
    api_success_rates = {}
    for result in results:
        for api_name, counts in result["api_success_counts"].items():
            if api_name not in api_success_rates:
                api_success_rates[api_name] = {"success": 0, "total": 0}
            api_success_rates[api_name]["success"] += counts["success"]
            api_success_rates[api_name]["total"] += counts["total"]

    # API별 성공률 계산
    for api_name, counts in api_success_rates.items():
        if counts["total"] > 0:
            success_rate = (counts["success"] / counts["total"]) * 100
            api_success_rates[api_name]["rate"] = success_rate
            print(f"{api_name} API 전체 성공률: {success_rate:.2f}% ({counts['success']}/{counts['total']})")

    # API 테스트 세트 성공률 계산
    api_set_success_rate = (set_success_count / total_sets) * 100 if total_sets > 0 else 0

    print(f"\nAPI 테스트 총 소요 시간: {api_test_time:.2f}초")
    print(f"성공적으로 완료된 API 테스트 세트: {set_success_count}/{total_sets} ({api_set_success_rate:.2f}%)")
    if total_sets > 0:
        print(f"평균 세트 처리 시간: {api_test_time / total_sets:.2f}초/세트")

    # 결과 반환
    return {
        'auth_success_count': auth_success_count,
        'auth_total_count': concurrent_users,
        'auth_success_rate': auth_success_rate,
        'api_set_success_count': set_success_count,
        'api_set_total_count': total_sets,
        'api_set_success_rate': api_set_success_rate,
        'api_success_rates': api_success_rates,
        'concurrent_users': concurrent_users,
        'set_count': set_count
    }