"""
모듈 설명: 통계 및 결과 처리 기능
"""
import statistics
import json
import os
from datetime import datetime

from . import config
from . import utils

def print_set_execution_statistics():
    """세트 실행 시간에 대한 통계 계산 및 출력"""
    if not utils.set_execution_times:
        return

    print(f"\n[세트 실행 시간 통계 (총 {len(utils.set_execution_times)} 세트)]")
    print(f"  한 세트당 최소 실행 시간: {min(utils.set_execution_times):.3f}초")
    print(f"  한 세트당 최대 실행 시간: {max(utils.set_execution_times):.3f}초")
    print(f"  한 세트당 평균 실행 시간: {statistics.mean(utils.set_execution_times):.3f}초")

    if len(utils.set_execution_times) > 1:
        print(f"  한 세트당 표준 편차: {statistics.stdev(utils.set_execution_times):.3f}초")

    # 한 세트를 처리하는데 평균 소요 시간 계산
    avg_seconds_per_set = statistics.mean(utils.set_execution_times)
    print(f"  한 세트당 평균 처리 시간: {avg_seconds_per_set:.3f}초/세트")

    print("\n" + "-" * 50)

def print_api_statistics(api_name, times, index, concurrent_users, set_count):
    """특정 API에 대한 통계 계산 및 출력"""
    if not times:
        return

    # 인증 관련 API와 일반 API 구분
    auth_apis = ["CreateToken", "ConnectProvider"]
    is_auth_api = api_name in auth_apis

    # 호출 횟수 계산 방식 설명 추가
    if is_auth_api:
        call_explanation = f"동시 사용자 수({concurrent_users})만큼 호출"
    else:
        call_explanation = f"동시 사용자 수({concurrent_users}) × 세트 수({set_count}) = {concurrent_users * set_count}회 호출"

    print(f"\n[{index}. {api_name} API 통계 (총 {len(times)}회, {call_explanation})]")
    print(f"  최소 응답 시간: {min(times):.3f}초")
    print(f"  최대 응답 시간: {max(times):.3f}초")
    print(f"  평균 응답 시간: {statistics.mean(times):.3f}초")

    if len(times) > 1:
        print(f"  표준 편차: {statistics.stdev(times):.3f}초")

    # 처리량 계산 (초당 요청 수)
    total_time = sum(times)
    if total_time > 0:
        requests_per_second = len(times) / total_time
        print(f"  처리량: {requests_per_second:.2f} 요청/초")

def print_statistics():
    """테스트 결과 통계 출력"""
    # 인증 API와 일반 API 구분하여 호출 횟수 계산
    auth_apis = ["CreateToken", "ConnectProvider"]
    auth_calls = sum(len(times) for api_name, times in utils.api_times.items() if api_name in auth_apis)
    regular_calls = sum(len(times) for api_name, times in utils.api_times.items() if api_name not in auth_apis)
    total_calls = auth_calls + regular_calls

    # 동시 사용자 수와 세트 수 추정 (측정된 데이터로부터)
    estimated_concurrent_users = auth_calls // 2  # CreateToken과 ConnectProvider 각각 호출
    if regular_calls > 0 and estimated_concurrent_users > 0:
        num_apis = 10  # CheckAppVersion, GetTimestamp 등 10개 API
        estimated_set_count = regular_calls // (estimated_concurrent_users * num_apis)
    else:
        estimated_set_count = 0

    print("\n" + "=" * 50)
    print("부하 테스트 결과 통계")
    print("=" * 50)

    print(f"동시 사용자: {estimated_concurrent_users}명")
    print(f"사용자당 API 테스트 세트: {estimated_set_count}개")
    print(f"총 테스트 세트: {estimated_concurrent_users * estimated_set_count}개")
    print(f"총 API 호출 횟수: {total_calls}회 (인증 {auth_calls}회 + 테스트 {regular_calls}회)")
    print(f"서버: {config.BASE_URL}")
    print("=" * 50)

    # 세트 실행 시간 통계 출력
    print_set_execution_statistics()

    # 각 API별 통계 출력 (넘버링 추가)
    for idx, (api_name, times) in enumerate(sorted(utils.api_times.items()), 1):
        print_api_statistics(api_name, times, idx, estimated_concurrent_users, estimated_set_count)

    # 전체 오류 통계
    total_errors = len(utils.errors)
    total_requests = sum(len(times) for times in utils.api_times.values())

    print(f"\n[오류 통계]")
    print(f"  총 오류 수: {total_errors}")

    if total_requests > 0:
        error_rate = (total_errors / total_requests) * 100
        print(f"  오류율: {error_rate:.2f}%")

    if utils.errors:
        print("\n[오류 목록 (최대 10개)]")
        for error in utils.errors[:10]:  # 첫 10개 오류만 표시
            print(f"  - {error}")

        if len(utils.errors) > 10:
            print(f"  ... 그 외 {len(utils.errors) - 10}개 오류")


def save_results_to_file(concurrent_users, set_count=1, save_summary=True, save_details_json=False):
    """테스트 결과를 파일로 저장

    Args:
        concurrent_users (int): 동시 사용자 수
        set_count (int, optional): 사용자당 테스트 세트 수. 기본값은 1.
        save_summary (bool, optional): 요약 통계 파일 저장 여부. 기본값은 True.
        save_details_json (bool, optional): 요청/응답 상세 JSON 로그 파일 저장 여부. 기본값은 False.
    """
    utils.ensure_directory_exists(config.LOG_DIR)

    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 총 테스트 세트 및 요청 수 계산
    total_sets = concurrent_users * set_count

    # 인증 API와 일반 API 구분하여 호출 횟수 계산
    auth_apis = ["CreateToken", "ConnectProvider"]
    auth_calls = sum(len(times) for api_name, times in utils.api_times.items() if api_name in auth_apis)
    regular_calls = sum(len(times) for api_name, times in utils.api_times.items() if api_name not in auth_apis)
    total_calls = auth_calls + regular_calls

    total_requests = sum(len(times) for times in utils.api_times.values())
    total_errors = len(utils.errors)

    # 요약 통계 파일 저장
    if save_summary:
        summary_filename = os.path.join(config.LOG_DIR, f"{now}_load_test_results_{concurrent_users}users_{set_count}sets.txt")

        with open(summary_filename, "w", encoding="utf-8-sig") as f:
            f.write("=" * 50 + "\n")
            f.write(f"부하 테스트 결과\n")
            f.write(f"동시 사용자: {concurrent_users}명\n")
            f.write(f"사용자당 API 테스트 세트: {set_count}개\n")
            f.write(f"총 테스트 세트: {total_sets}개\n")
            f.write(f"총 API 호출 횟수: {total_calls}회 (인증 {auth_calls}회 + 테스트 {regular_calls}회)\n")
            f.write(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"서버: {config.BASE_URL}\n")
            f.write("=" * 50 + "\n\n")

            # 세트 실행 시간 통계 기록
            if utils.set_execution_times:
                f.write(f"[세트 실행 시간 통계 (총 {len(utils.set_execution_times)} 세트)]\n")
                f.write(f"  한 세트당 최소 실행 시간: {min(utils.set_execution_times):.3f}초\n")
                f.write(f"  한 세트당 최대 실행 시간: {max(utils.set_execution_times):.3f}초\n")
                f.write(f"  한 세트당 평균 실행 시간: {statistics.mean(utils.set_execution_times):.3f}초\n")

                if len(utils.set_execution_times) > 1:
                    f.write(f"  한 세트당 표준 편차: {statistics.stdev(utils.set_execution_times):.3f}초\n")

                avg_seconds_per_set = statistics.mean(utils.set_execution_times)
                f.write(f"  한 세트당 평균 처리 시간: {avg_seconds_per_set:.3f}초/세트\n")

                f.write("\n" + "-" * 50 + "\n")

            # 각 API별 통계 기록 (넘버링 추가)
            for idx, (api_name, times) in enumerate(sorted(utils.api_times.items()), 1):
                if not times:
                    continue

                # 인증 관련 API와 일반 API 구분
                auth_apis = ["CreateToken", "ConnectProvider"]
                is_auth_api = api_name in auth_apis

                # 호출 횟수 계산 방식 설명 추가
                if is_auth_api:
                    call_explanation = f"동시 사용자 수({concurrent_users})만큼 호출"
                else:
                    call_explanation = f"동시 사용자 수({concurrent_users}) × 세트 수({set_count}) = {concurrent_users * set_count}회 호출"

                f.write(f"[{idx}. {api_name} API 통계 (총 {len(times)}회, {call_explanation})]\n")
                f.write(f"  최소 응답 시간: {min(times):.3f}초\n")
                f.write(f"  최대 응답 시간: {max(times):.3f}초\n")
                f.write(f"  평균 응답 시간: {statistics.mean(times):.3f}초\n")

                if len(times) > 1:
                    f.write(f"  표준 편차: {statistics.stdev(times):.3f}초\n")

                total_time = sum(times)
                if total_time > 0:
                    requests_per_second = len(times) / total_time
                    f.write(f"  처리량: {requests_per_second:.2f} 요청/초\n")

                f.write("\n")

            # 전체 오류 통계
            f.write(f"[오류 통계]\n")
            f.write(f"  총 오류 수: {total_errors}\n")

            if total_requests > 0:
                error_rate = (total_errors / total_requests) * 100
                f.write(f"  오류율: {error_rate:.2f}%\n")

            if utils.errors:
                f.write("\n[오류 목록]\n")
                for error in utils.errors:
                    f.write(f"  - {error}\n")

        print(f"\n요약 결과가 '{summary_filename}' 파일에 저장되었습니다.")

    # 상세 로그 (JSON 형식) 저장
    if save_details_json:
        detailed_filename = os.path.join(config.LOG_DIR, f"{now}_load_test_detailed_{concurrent_users}users_{set_count}sets.json")

        try:
            with open(detailed_filename, "w", encoding="utf-8-sig") as f:
                # 로그 메타데이터 추가
                log_data = {
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "concurrent_users": concurrent_users,
                        "sets_per_user": set_count,
                        "total_sets": total_sets,
                        "total_api_calls": total_calls,
                        "auth_calls": auth_calls,
                        "test_calls": regular_calls,
                        "server": config.BASE_URL,
                        "test_duration": sum(sum(times) for times in utils.api_times.values()),
                        "total_requests": total_requests,
                        "total_errors": total_errors
                    },
                    "requests": utils.detailed_logs
                }

                # JSON으로 직렬화할 수 없는 객체 확인 및 제거
                json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)

            print(f"상세 로그가 '{detailed_filename}' 파일에 저장되었습니다.")
        except Exception as e:
            print(f"상세 로그 저장 중 오류 발생: {str(e)}")