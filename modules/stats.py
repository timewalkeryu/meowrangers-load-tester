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
    print("[부하 테스트 결과]")
    print("")
    print(f"- 동시 사용자: {estimated_concurrent_users}명")
    print(f"- 사용자당 API 테스트 세트: {estimated_set_count}개")
    print(f"- 총 테스트 세트: {estimated_concurrent_users * estimated_set_count}개")
    print("")
    print(f"총 API 호출 횟수: {total_calls}회")
    print(f"- 인증 과정 API 호출: {auth_calls}회")
    print(f"- 테스트 세트 API 호출: {regular_calls}회")
    print(f"서버: {config.BASE_URL}")
    print("=" * 50)

    # 세트 실행 시간 통계 출력
    print_set_execution_statistics()

    # 인증 과정과 API 테스트 세트 구분하여 통계 출력
    print("\n" + "=" * 50)
    print("[1. 인증 과정 통계]")

    # 인증 과정 API 통계
    auth_api_times = {api_name: times for api_name, times in utils.api_times.items() if api_name in auth_apis}
    auth_total_calls = sum(len(times) for times in auth_api_times.values())
    auth_errors = [err for err in utils.errors if any(api in err for api in auth_apis)]
    auth_error_rate = (len(auth_errors) / auth_total_calls * 100) if auth_total_calls > 0 else 0

    print(f"총 인증 API 호출 횟수: {auth_total_calls}회")
    print(f"인증 과정 오류 수: {len(auth_errors)}개")
    print(f"인증 과정 오류율: {auth_error_rate:.2f}%")
    print(f"인증 과정 성공률: {100 - auth_error_rate:.2f}%")

    # 인증 과정에서 실패한 사용자 수 계산
    create_token_errors = len([err for err in utils.errors if "CreateToken" in err])
    connect_provider_errors = len([err for err in utils.errors if "ConnectProvider" in err])
    estimated_failed_users = create_token_errors + connect_provider_errors // 2  # 대략적인 추정
    estimated_success_users = estimated_concurrent_users - estimated_failed_users

    print(f"인증 성공 사용자: 약 {estimated_success_users}명/{estimated_concurrent_users}명 ({estimated_success_users/estimated_concurrent_users*100:.2f}%)")

    if auth_errors:
        print("\n인증 과정 오류 샘플 (최대 5개):")
        for error in auth_errors[:5]:
            print(f"  - {error}")
        if len(auth_errors) > 5:
            print(f"  ... 그 외 {len(auth_errors) - 5}개 오류")

    print("\n" + "-" * 50)

    # API 테스트 세트 통계
    print("\n[2. API 테스트 세트 통계]")

    regular_api_times = {api_name: times for api_name, times in utils.api_times.items() if api_name not in auth_apis}
    regular_total_calls = sum(len(times) for times in regular_api_times.values())
    regular_errors = [err for err in utils.errors if not any(api in err for api in auth_apis)]
    regular_error_rate = (len(regular_errors) / regular_total_calls * 100) if regular_total_calls > 0 else 0

    print(f"총 테스트 API 호출 횟수: {regular_total_calls}회")
    print(f"테스트 API 오류 수: {len(regular_errors)}개")
    print(f"테스트 API 오류율: {regular_error_rate:.2f}%")
    print(f"테스트 API 성공률: {100 - regular_error_rate:.2f}%")

    if utils.set_execution_times:
        total_sets = len(utils.set_execution_times)
        total_api_per_set = regular_total_calls // total_sets if total_sets > 0 else 0
        print(f"총 실행된 테스트 세트 수: {total_sets}개")
        print(f"세트당 평균 API 호출 수: {total_api_per_set}개")

    if regular_errors:
        print("\n테스트 API 오류 샘플 (최대 5개):")
        for error in regular_errors[:5]:
            print(f"  - {error}")
        if len(regular_errors) > 5:
            print(f"  ... 그 외 {len(regular_errors) - 5}개 오류")

    print("\n" + "-" * 50)

    # 각 API별 통계 출력 (넘버링 추가)
    print("\n[3. 개별 API 상세 통계]")
    for idx, (api_name, times) in enumerate(sorted(utils.api_times.items()), 1):
        print_api_statistics(api_name, times, idx, estimated_concurrent_users, estimated_set_count)

    # 전체 오류 통계
    print("\n" + "=" * 50)
    print("[전체 테스트 요약]")

    total_errors = len(utils.errors)
    total_requests = sum(len(times) for times in utils.api_times.values())
    total_error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0

    print(f"총 API 요청 수: {total_requests}회")
    print(f"총 오류 수: {total_errors}개")
    print(f"전체 오류율: {total_error_rate:.2f}%")
    print(f"전체 성공률: {100 - total_error_rate:.2f}%")

    # 테스트 결과 판정
    print("\n[테스트 결과 판정]")
    if auth_error_rate > 5.0:
        print(f"❌ 인증 과정 오류율({auth_error_rate:.2f}%)이 허용 임계값(5.0%)을 초과했습니다.")
    else:
        print(f"✅ 인증 과정 오류율: {auth_error_rate:.2f}%")

    if regular_error_rate > 5.0:
        print(f"❌ 테스트 API 오류율({regular_error_rate:.2f}%)이 허용 임계값(5.0%)을 초과했습니다.")
    else:
        print(f"✅ 테스트 API 오류율: {regular_error_rate:.2f}%")

    if total_error_rate > 5.0:
        print(f"❌ 전체 오류율({total_error_rate:.2f}%)이 허용 임계값(5.0%)을 초과했습니다.")
    else:
        print(f"✅ 전체 오류율: {total_error_rate:.2f}%")

    if estimated_success_users/estimated_concurrent_users < 0.95:
        print(f"❌ 인증 성공 사용자 비율({estimated_success_users/estimated_concurrent_users*100:.2f}%)이 최소 요구치(95.0%)보다 낮습니다.")
    else:
        print(f"✅ 인증 성공 사용자 비율: {estimated_success_users/estimated_concurrent_users*100:.2f}%")


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

    # 인증 과정 오류와 API 테스트 세트 오류 구분
    auth_errors = [err for err in utils.errors if any(api in err for api in auth_apis)]
    regular_errors = [err for err in utils.errors if not any(api in err for api in auth_apis)]

    auth_error_rate = (len(auth_errors) / auth_calls * 100) if auth_calls > 0 else 0
    regular_error_rate = (len(regular_errors) / regular_calls * 100) if regular_calls > 0 else 0
    total_error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

    # 인증 성공 사용자 수 계산
    create_token_errors = len([err for err in utils.errors if "CreateToken" in err])
    connect_provider_errors = len([err for err in utils.errors if "ConnectProvider" in err])
    estimated_failed_users = create_token_errors + connect_provider_errors // 2  # 대략적인 추정
    estimated_success_users = concurrent_users - estimated_failed_users
    auth_success_rate = (estimated_success_users / concurrent_users * 100) if concurrent_users > 0 else 0

    # 요약 통계 파일 저장
    if save_summary:
        summary_filename = os.path.join(config.LOG_DIR, f"{now}_load_test_results_{concurrent_users}users_{set_count}sets.txt")

        with open(summary_filename, "w", encoding="utf-8-sig") as f:
            f.write("=" * 50 + "\n")
            f.write("[부하 테스트 결과]\n\n")
            f.write(f"- 동시 사용자: {concurrent_users}명\n")
            f.write(f"- 사용자당 API 테스트 세트: {set_count}개\n")
            f.write(f"- 총 테스트 세트: {total_sets}개\n\n")
            f.write(f"총 API 호출 횟수: {total_calls}회\n")
            f.write(f"- 인증 과정 API 호출: {auth_calls}회\n")
            f.write(f"- 테스트 세트 API 호출: {regular_calls}회\n")
            f.write(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"서버: {config.BASE_URL}\n")
            f.write("=" * 50 + "\n\n")

            # 인증 과정 통계
            f.write("=" * 50 + "\n")
            f.write("[1. 인증 과정 통계]\n\n")
            f.write(f"총 인증 API 호출 횟수: {auth_calls}회\n")
            f.write(f"인증 과정 오류 수: {len(auth_errors)}개\n")
            f.write(f"인증 과정 오류율: {auth_error_rate:.2f}%\n")
            f.write(f"인증 과정 성공률: {100 - auth_error_rate:.2f}%\n")
            f.write(f"인증 성공 사용자: 약 {estimated_success_users}명/{concurrent_users}명 ({auth_success_rate:.2f}%)\n")

            if auth_errors:
                f.write("\n인증 과정 오류 샘플 (최대 10개):\n")
                for error in auth_errors[:10]:
                    f.write(f"  - {error}\n")
                if len(auth_errors) > 10:
                    f.write(f"  ... 그 외 {len(auth_errors) - 10}개 오류\n")

            f.write("\n" + "-" * 50 + "\n")

            # API 테스트 세트 통계
            f.write("\n[2. API 테스트 세트 통계]\n\n")
            f.write(f"총 테스트 API 호출 횟수: {regular_calls}회\n")
            f.write(f"테스트 API 오류 수: {len(regular_errors)}개\n")
            f.write(f"테스트 API 오류율: {regular_error_rate:.2f}%\n")
            f.write(f"테스트 API 성공률: {100 - regular_error_rate:.2f}%\n")

            if utils.set_execution_times:
                total_exec_sets = len(utils.set_execution_times)
                total_api_per_set = regular_calls // total_exec_sets if total_exec_sets > 0 else 0
                f.write(f"총 실행된 테스트 세트 수: {total_exec_sets}개\n")
                f.write(f"세트당 평균 API 호출 수: {total_api_per_set}개\n")

            if regular_errors:
                f.write("\n테스트 API 오류 샘플 (최대 10개):\n")
                for error in regular_errors[:10]:
                    f.write(f"  - {error}\n")
                if len(regular_errors) > 10:
                    f.write(f"  ... 그 외 {len(regular_errors) - 10}개 오류\n")

            f.write("\n" + "-" * 50 + "\n")

            # 세트 실행 시간 통계 기록
            if utils.set_execution_times:
                f.write(f"\n[세트 실행 시간 통계 (총 {len(utils.set_execution_times)} 세트)]\n")
                f.write(f"  한 세트당 최소 실행 시간: {min(utils.set_execution_times):.3f}초\n")
                f.write(f"  한 세트당 최대 실행 시간: {max(utils.set_execution_times):.3f}초\n")
                f.write(f"  한 세트당 평균 실행 시간: {statistics.mean(utils.set_execution_times):.3f}초\n")

                if len(utils.set_execution_times) > 1:
                    f.write(f"  한 세트당 표준 편차: {statistics.stdev(utils.set_execution_times):.3f}초\n")

                avg_seconds_per_set = statistics.mean(utils.set_execution_times)
                f.write(f"  한 세트당 평균 처리 시간: {avg_seconds_per_set:.3f}초/세트\n")

                f.write("\n" + "-" * 50 + "\n")

            # 각 API별 통계 기록
            f.write("\n[3. 개별 API 상세 통계]\n")
            for idx, (api_name, times) in enumerate(sorted(utils.api_times.items()), 1):
                if not times:
                    continue

                # 인증 관련 API와 일반 API 구분
                is_auth_api = api_name in auth_apis

                # 호출 횟수 계산 방식 설명 추가
                if is_auth_api:
                    call_explanation = f"동시 사용자 수({concurrent_users})만큼 호출"
                else:
                    call_explanation = f"동시 사용자 수({concurrent_users}) × 세트 수({set_count}) = {concurrent_users * set_count}회 호출"

                f.write(f"\n[{idx}. {api_name} API 통계 (총 {len(times)}회, {call_explanation})]\n")
                f.write(f"  최소 응답 시간: {min(times):.3f}초\n")
                f.write(f"  최대 응답 시간: {max(times):.3f}초\n")
                f.write(f"  평균 응답 시간: {statistics.mean(times):.3f}초\n")

                if len(times) > 1:
                    f.write(f"  표준 편차: {statistics.stdev(times):.3f}초\n")

                total_time = sum(times)
                if total_time > 0:
                    requests_per_second = len(times) / total_time
                    f.write(f"  처리량: {requests_per_second:.2f} 요청/초\n")

            # 전체 오류 통계
            f.write("\n" + "=" * 50 + "\n")
            f.write("[전체 테스트 요약]\n\n")
            f.write(f"총 API 요청 수: {total_requests}회\n")
            f.write(f"총 오류 수: {total_errors}개\n")
            f.write(f"전체 오류율: {total_error_rate:.2f}%\n")
            f.write(f"전체 성공률: {100 - total_error_rate:.2f}%\n")

            # 테스트 결과 판정
            f.write("\n[테스트 결과 판정]\n")
            if auth_error_rate > 5.0:
                f.write(f"❌ 인증 과정 오류율({auth_error_rate:.2f}%)이 허용 임계값(5.0%)을 초과했습니다.\n")
            else:
                f.write(f"✅ 인증 과정 오류율: {auth_error_rate:.2f}%\n")

            if regular_error_rate > 5.0:
                f.write(f"❌ 테스트 API 오류율({regular_error_rate:.2f}%)이 허용 임계값(5.0%)을 초과했습니다.\n")
            else:
                f.write(f"✅ 테스트 API 오류율: {regular_error_rate:.2f}%\n")

            if total_error_rate > 5.0:
                f.write(f"❌ 전체 오류율({total_error_rate:.2f}%)이 허용 임계값(5.0%)을 초과했습니다.\n")
            else:
                f.write(f"✅ 전체 오류율: {total_error_rate:.2f}%\n")

            if auth_success_rate < 95.0:
                f.write(f"❌ 인증 성공 사용자 비율({auth_success_rate:.2f}%)이 최소 요구치(95.0%)보다 낮습니다.\n")
            else:
                f.write(f"✅ 인증 성공 사용자 비율: {auth_success_rate:.2f}%\n")

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
                        "total_errors": total_errors,
                        "auth_errors": len(auth_errors),
                        "api_errors": len(regular_errors),
                        "auth_error_rate": auth_error_rate,
                        "api_error_rate": regular_error_rate,
                        "total_error_rate": total_error_rate,
                        "auth_success_users": estimated_success_users,
                        "auth_success_rate": auth_success_rate
                    },
                    "requests": utils.detailed_logs
                }

                # JSON으로 직렬화할 수 없는 객체 확인 및 제거
                json.dump(log_data, f, ensure_ascii=False, indent=2, default=str)

            print(f"상세 로그가 '{detailed_filename}' 파일에 저장되었습니다.")
        except Exception as e:
            print(f"상세 로그 저장 중 오류 발생: {str(e)}")