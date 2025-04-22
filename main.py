#!/usr/bin/env python
"""
게임 서버 부하 테스트 도구

이 스크립트는 게임 서버의 성능을 테스트하기 위한 도구입니다.
설정된 수의 가상 사용자를 생성하여 API 호출을 병렬로 실행하고 결과를 분석합니다.
"""
import asyncio
import argparse
import time
import sys
import os

# 스크립트 실행 경로와 관계없이 모듈을 찾을 수 있도록 설정
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from modules import config, test_runner, stats, utils
except ImportError:
    print("모듈을 찾을 수 없습니다. 올바른 디렉토리에서 실행 중인지 확인하세요.")
    sys.exit(1)


def parse_arguments():
    """커맨드라인 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="게임 서버 부하 테스트 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
예시:
  python main.py                    # 기본값({config.DEFAULT_CONCURRENT_USERS}명, {config.DEFAULT_TEST_SETS}세트)으로 개발 환경 테스트
  python main.py 200                # 200명의 동시 사용자로 개발 환경 테스트 (기본 {config.DEFAULT_TEST_SETS}세트)
  python main.py 100 10             # 100명의 동시 사용자, 각 사용자당 10세트 API 호출 (개발 환경)
  python main.py 100 10 --env qa    # 100명의 동시 사용자, 각 사용자당 10세트 API 호출 (QA 환경)
  python main.py -h, --help         # 도움말 표시

서버 환경 옵션:
  --env dev,qa,live                 # 테스트할 서버 환경 (기본: dev)

추가 옵션:
  --no-summary                      # 요약 통계 파일 생성 비활성화
  --detailed-json                   # 상세 JSON 로그 파일 생성
  --error-threshold PERCENT         # 오류율 임계값 설정 (기본: {config.ERROR_THRESHOLD}%)
  --min-success-rate PERCENT        # 최소 성공률 설정 (기본: {config.MIN_SUCCESS_RATE}%)

출력 파일:
  log/load_test_results_[사용자수]users_[세트수]sets_[시간].txt   # 요약 결과
  log/load_test_detailed_[사용자수]users_[세트수]sets_[시간].json  # 상세 로그
        """
    )

    parser.add_argument("users", type=int, nargs='?', default=config.DEFAULT_CONCURRENT_USERS,
                        help=f"동시 테스트할 사용자 수 (기본값: {config.DEFAULT_CONCURRENT_USERS})")

    parser.add_argument("sets", type=int, nargs='?', default=config.DEFAULT_TEST_SETS,
                        help=f"각 사용자당 실행할 API 테스트 세트 수 (기본값: {config.DEFAULT_TEST_SETS})")

    parser.add_argument("--env", choices=["dev", "qa", "live"], default="dev",
                        help="테스트할 서버 환경 (dev, qa, live)")

    parser.add_argument("--no-summary", action="store_true",
                        help="요약 통계 파일 생성 비활성화")

    parser.add_argument("--detailed-json", action="store_true",
                        help="상세 JSON 로그 파일 생성")

    parser.add_argument("--error-threshold", type=float, default=config.ERROR_THRESHOLD,
                        help=f"허용 가능한 최대 오류율(퍼센트), 이 값 초과 시 비정상 종료 (기본값: {config.ERROR_THRESHOLD}%%)")

    parser.add_argument("--min-success-rate", type=float, default=config.MIN_SUCCESS_RATE,
                        help=f"필요한 최소 성공률(퍼센트), 이 값 미만 시 비정상 종료 (기본값: {config.MIN_SUCCESS_RATE}%%)")

    return parser.parse_args()


async def main_async(concurrent_users, set_count, save_summary, save_details_json):
    """비동기 메인 함수"""
    # 테스트 실행
    test_results = await test_runner.run_load_test(concurrent_users, set_count)

    # 테스트 결과 저장
    stats.save_results_to_file(
        concurrent_users,
        set_count,
        save_summary=save_summary,
        save_details_json=save_details_json
    )

    return test_results


def main():
    """메인 함수"""
    # 커맨드라인 인자 파싱
    args = parse_arguments()
    concurrent_users = args.users
    set_count = args.sets
    save_summary = not args.no_summary
    save_details_json = args.detailed_json
    error_threshold = args.error_threshold
    min_success_rate = args.min_success_rate

    # 서버 환경 설정
    if args.env and args.env in config.SERVER_ENVIRONMENTS:
        config.BASE_URL = config.SERVER_ENVIRONMENTS[args.env]
        print(f"서버 환경을 '{args.env}'으로 설정합니다: {config.BASE_URL}")

    if concurrent_users <= 0:
        print("오류: 동시 사용자 수는 1 이상이어야 합니다.")
        sys.exit(1)

    if set_count <= 0:
        print("오류: API 테스트 세트 수는 1 이상이어야 합니다.")
        sys.exit(1)

    print("=" * 50)
    print(f"게임 서버 부하 테스트 시작")
    print(f"동시 사용자: {concurrent_users}명")
    print(f"사용자당 API 테스트 세트: {set_count}개")
    print(f"총 테스트 세트 수: {concurrent_users * set_count}개")
    print(f"서버 환경: {args.env} ({config.BASE_URL})")
    print(f"최대 허용 오류율: {error_threshold}%")
    print(f"최소 필요 성공률: {min_success_rate}%")
    print(f"요약 통계 파일: {'생성' if save_summary else '비활성화'}")
    print(f"상세 JSON 로그: {'생성' if save_details_json else '비활성화'}")
    print("=" * 50)

    start_time = time.time()

    # 비동기 테스트 실행
    test_results = asyncio.run(main_async(concurrent_users, set_count, save_summary, save_details_json))

    # 테스트 종료 및 통계 출력
    total_time = time.time() - start_time
    print(f"\n테스트 완료! 총 소요 시간: {total_time:.2f}초")

    # 통계 출력 (기존 함수 그대로 호출)
    stats.print_statistics()

    # 성공/실패 판정
    is_successful = True

    print("\n" + "=" * 50)
    print("[최종 테스트 결과 판정]")

    # 1. 인증 과정 성공률 체크
    auth_success_rate = test_results.get('auth_success_rate', 0)
    if auth_success_rate < min_success_rate:
        print(f"❌ 인증 API 성공률({auth_success_rate:.2f}%)이 최소 요구치({min_success_rate}%)보다 낮습니다.")
        print(f"   - 성공: {test_results.get('auth_success_count', 0)}/{test_results.get('auth_total_count', 0)} 사용자")
        is_successful = False
    else:
        print(f"✅ 인증 API 성공률: {auth_success_rate:.2f}%")
        print(f"   - 성공: {test_results.get('auth_success_count', 0)}/{test_results.get('auth_total_count', 0)} 사용자")

    # 2. API 테스트 세트 성공률 체크
    api_set_success_rate = test_results.get('api_set_success_rate', 0)
    if api_set_success_rate < min_success_rate:
        print(f"❌ 나머지 API 세트 성공률({api_set_success_rate:.2f}%)이 최소 요구치({min_success_rate}%)보다 낮습니다.")
        print(f"   - 성공: {test_results.get('api_set_success_count', 0)}/{test_results.get('api_set_total_count', 0)} 세트")
        is_successful = False
    else:
        print(f"✅ 나머지 API 세트 성공률: {api_set_success_rate:.2f}%")
        print(f"   - 성공: {test_results.get('api_set_success_count', 0)}/{test_results.get('api_set_total_count', 0)} 세트")

    # 3. 각 API별 성공률 출력 (옵션)
    api_success_rates = test_results.get('api_success_rates', {})
    if api_success_rates:
        print(f"\n[개별 API 성공률]")
        for api_name, data in sorted(api_success_rates.items()):
            rate = data.get('rate', 0)
            success = data.get('success', 0)
            total = data.get('total', 0)
            if rate < min_success_rate:
                print(f"❌ {api_name}: {rate:.2f}% ({success}/{total})")
                is_successful = False
            else:
                print(f"✅ {api_name}: {rate:.2f}% ({success}/{total})")

    # 4. 오류율 계산 - API 성공 데이터 기반
    auth_apis = ["CreateToken", "ConnectProvider"]

    # API 성공률 기반 오류 계산 (명확한 success 필드 사용)
    api_success_failures = {}
    for api_name in utils.api_times.keys():
        # is_success 필드를 기준으로 성공 여부 판단
        api_success_count = len([log for log in utils.detailed_logs if log.get('api_name') == api_name and log.get('is_success') is True])
        api_total_count = len([log for log in utils.detailed_logs if log.get('api_name') == api_name])
        api_success_failures[api_name] = {
            'success': api_success_count,
            'total': api_total_count
        }

    # 인증 API 오류
    auth_success = sum(api_success_failures.get(api, {}).get('success', 0) for api in auth_apis)
    auth_total = sum(api_success_failures.get(api, {}).get('total', 0) for api in auth_apis)
    auth_error_rate = ((auth_total - auth_success) / auth_total * 100) if auth_total > 0 else 0

    # 나머지 API 오류
    regular_apis = [api for api in api_success_failures.keys() if api not in auth_apis]
    regular_success = sum(api_success_failures.get(api, {}).get('success', 0) for api in regular_apis)
    regular_total = sum(api_success_failures.get(api, {}).get('total', 0) for api in regular_apis)
    regular_error_rate = ((regular_total - regular_success) / regular_total * 100) if regular_total > 0 else 0

    # 전체 오류율
    total_success = auth_success + regular_success
    total_calls = auth_total + regular_total
    total_error_rate = ((total_calls - total_success) / total_calls * 100) if total_calls > 0 else 0

    # 5. 오류율 판정 - HTTP 상태 코드 기반
    print(f"\n[오류율 판정]")
    if auth_error_rate > error_threshold:
        print(f"❌ 인증 API 오류율({auth_error_rate:.2f}%)이 허용 임계값({error_threshold}%)을 초과했습니다.")
        print(f"   - 오류: {auth_total - auth_success}/{auth_total} 호출")
        is_successful = False
    else:
        print(f"✅ 인증 API 오류율: {auth_error_rate:.2f}%")
        print(f"   - 오류: {auth_total - auth_success}/{auth_total} 호출")

    if regular_error_rate > error_threshold:
        print(f"❌ 나머지 API 오류율({regular_error_rate:.2f}%)이 허용 임계값({error_threshold}%)을 초과했습니다.")
        print(f"   - 오류: {regular_total - regular_success}/{regular_total} 호출")
        is_successful = False
    else:
        print(f"✅ 나머지 API 오류율: {regular_error_rate:.2f}%")
        print(f"   - 오류: {regular_total - regular_success}/{regular_total} 호출")

    if total_error_rate > error_threshold:
        print(f"❌ 전체 오류율({total_error_rate:.2f}%)이 허용 임계값({error_threshold}%)을 초과했습니다.")
        print(f"   - 오류: {total_calls - total_success}/{total_calls} 호출")
        is_successful = False
    else:
        print(f"✅ 전체 오류율: {total_error_rate:.2f}%")
        print(f"   - 오류: {total_calls - total_success}/{total_calls} 호출")

    # 최종 결과 출력 및 종료 코드 설정
    print("\n" + "=" * 50)
    if is_successful:
        print("\n✅ 부하 테스트 최종 결과: 성공")
        return 0  # 성공 시 종료 코드 0
    else:
        print("\n❌ 부하 테스트 최종 결과: 실패")
        return 1  # 실패 시 종료 코드 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)  # 명시적으로 종료 코드 설정
    except KeyboardInterrupt:
        print("\n테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(2)  # 사용자 중단 시 종료 코드 2
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        sys.exit(3)  # 예외 발생 시 종료 코드 3