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
    from modules import config, test_runner, stats
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
  python main.py                    # 기본값({config.DEFAULT_CONCURRENT_USERS}명, {config.DEFAULT_TEST_SETS}세트)으로 테스트 실행
  python main.py 200                # 200명의 동시 사용자로 테스트 실행 (기본 {config.DEFAULT_TEST_SETS}세트)
  python main.py 100 10             # 100명의 동시 사용자, 각 사용자당 10세트 API 호출
  python main.py -h, --help         # 도움말 표시

출력 파일:
  log/load_test_results_[사용자수]users_[세트수]sets_[시간].txt   # 요약 결과
  log/load_test_detailed_[사용자수]users_[세트수]sets_[시간].json  # 상세 로그
        """
    )

    parser.add_argument("users", type=int, nargs='?', default=config.DEFAULT_CONCURRENT_USERS,
                        help=f"동시 테스트할 사용자 수 (기본값: {config.DEFAULT_CONCURRENT_USERS})")

    parser.add_argument("sets", type=int, nargs='?', default=config.DEFAULT_TEST_SETS,
                        help=f"각 사용자당 실행할 API 테스트 세트 수 (기본값: {config.DEFAULT_TEST_SETS})")

    return parser.parse_args()


async def main_async(concurrent_users, set_count):
    """비동기 메인 함수"""
    # 테스트 실행
    await test_runner.run_load_test(concurrent_users, set_count)


def main():
    """메인 함수"""
    # 커맨드라인 인자 파싱
    args = parse_arguments()
    concurrent_users = args.users
    set_count = args.sets

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
    print(f"서버: {config.BASE_URL}")
    print("=" * 50)

    start_time = time.time()

    # 비동기 테스트 실행
    asyncio.run(main_async(concurrent_users, set_count))

    # 테스트 종료 및 통계 출력
    total_time = time.time() - start_time
    print(f"\n테스트 완료! 총 소요 시간: {total_time:.2f}초")

    stats.print_statistics()
    stats.save_results_to_file(concurrent_users, set_count)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(0)
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        sys.exit(1)