# 국내 여행 추천 CLI

여행 날짜를 입력하면 **Gemini가 국내 지역을 추천**하고, **Kakao Local로 맛집을 검색**한 뒤 **Markdown 여행 리포트**를 생성하는 Python 프로그램입니다.

## 주요 기능

- argparse로 필수 `-date` 입력 및 날짜 형식·실제 날짜 검증
- 지역·날씨·행사 후보·추천 이유를 JSON으로 생성하고 키·타입 검증
- 추천 JSON 파싱/검증 실패 시 수정 프롬프트로 1회 재요청
- 추천 지역으로 음식점 후보 최대 5곳 검색
- 지도 API 실패·검색 0건에도 맛집을 `데이터 없음`으로 표시하고 진행
- 추천 이유·날씨·행사·맛집·오전/오후/저녁 일정 생성
- 오류를 JSON의 `errors`와 리포트의 errors 섹션에 반영
- `results/`에 JSON·Markdown 저장, 진행 로그와 저장 경로 출력

## 설치 및 API 설정

Python 3.11 이상이 필요합니다. Windows PowerShell 기준:

```powershell
git clone https://github.com/gaori2952/A1-2.git
cd A1-2
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

이미 프로젝트와 `.env`가 있다면 생성·복사 단계는 생략합니다. `.env`에 실제 키와 사용 가능한 모델 ID를 입력합니다.

```dotenv
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_AVAILABLE_MODEL_ID
KAKAO_REST_API_KEY=YOUR_KAKAO_REST_API_KEY
```

Gemini 설정은 [Google AI Studio](https://aistudio.google.com/), Kakao REST API 키는 [Kakao Developers](https://developers.kakao.com/)에서 준비합니다. 카카오맵 사용 설정을 확인합니다. 환경변수가 `.env`보다 우선하며 필수 설정이 없으면 외부 호출 전에 종료합니다.

**키 보안:** 키를 코드에 직접 쓰지 않고 `.env`·환경변수로 관리하여 소스와 비밀 값을 분리합니다. `.env`는 Git에서 제외하며 README·로그·결과·스크린샷에 실제 키를 노출하지 않습니다.

## 실행

```bash
python main.py -date "2026-10-15"
python main.py --help
```

`--date`도 지원합니다. `2026/10/15`, `2026-02-30` 등의 잘못된 입력은 사용법과 오류를 출력하고 종료합니다.

종료 코드: **0** 정상 리포트 저장 / **1** 설정·API·처리된 저장 오류 또는 대체 리포트 / **2** 입력 오류.

## 데이터 흐름

**날짜 검증 → Gemini 추천 JSON → recommended_city로 Kakao 검색 → Gemini 최종 리포트 → 결과 저장**

추천 JSON의 필수 필드는 `recommended_city: string`, `weather: string`, `events: string[]`, `reason: string`입니다. 행사 후보는 1~3개로 검증하고 이유는 프롬프트에서 2~4문장을 요청합니다. 추가 키·누락 키·잘못된 타입은 거부하고 문자열 앞뒤 공백을 제거합니다.

JSON을 사용하는 이유는 자유로운 설명에서 지역명을 추측하지 않고 **검증된 recommended_city를 다음 API의 입력으로 전달**하기 위해서입니다.

REST 요청은 URL·메서드·헤더·입력으로, 응답은 상태 코드·헤더·본문으로 구성됩니다. Gemini는 **POST** 본문으로 프롬프트와 설정을 보내 생성을 요청하고, Kakao는 **GET** 쿼리로 기존 장소를 조회합니다.

맛집은 `name`, `address`, `category`, `url`, `x`, `y`로 변환합니다. 좌표는 숫자로 저장하고 확보할 수 없으면 null로 둡니다. 실제 검색된 목록만 사용합니다.

## 프로젝트 구조

```text
A1-2/
├── main.py                  # 입력·설정 확인 후 전체 실행
├── README.md                # 소개, 설치·실행 및 결과 확인
├── .env.example             # 키·모델 설정 예시
├── .gitignore               # 비밀 파일·가상환경·결과 제외
├── requirements.txt         # requests, python-dotenv
├── requirements-dev.txt     # 실행 의존성 및 pytest
│
├── travel/
│   ├── __init__.py          # 패키지 초기화
│   ├── cli.py               # parse_args(): CLI와 날짜 검증 연결
│   ├── config.py            # load_settings(): 설정 로딩·누락 검사
│   ├── validation.py        # validate_date(), validate_recommendation()
│   ├── prompts.py           # 추천 JSON 스키마·추천 및 리포트 프롬프트
│   ├── llm.py               # Gemini 호출·응답 추출·추천 재요청
│   ├── places.py            # Kakao 검색·장소 정규화·좌표 변환
│   ├── pipeline.py          # 단계 연결·오류 누적·종료 코드 반환
│   ├── report.py            # 필수 섹션·일정 보완·맛집·오류 표시
│   ├── storage.py           # 실행 시각 기반 경로·결과 저장
│   └── errors.py            # TravelError와 오류 기록 형식
│
├── tests/
│   ├── test_cli.py          # 옵션·잘못된 날짜·종료 코드
│   ├── test_validation.py   # 날짜·추천 JSON 검증
│   ├── test_places.py       # 검색 조건·좌표·0건 결과
│   └── test_pipeline.py     # 재요청·지도 실패 후 진행·리포트
│
└── results/                 # 실행 시 생성, Git에서 제외
    ├── <실행시각>_<여행날짜>.json
    └── <실행시각>_<여행날짜>.md
```

## 오류 처리와 인증 점검

| 상황 | 처리·확인 |
| --- | --- |
| 키 미설정 | 누락 변수와 설정 방법 안내 후 즉시 종료 |
| 추천 JSON 오류 | 검증 문제를 포함한 수정 프롬프트로 1회 재요청 |
| Gemini 401/403 | 키, `x-goog-api-key` 헤더, 이용 권한 확인 |
| Kakao 401/403 | REST API 키, `Authorization: KakaoAK <키>` 형식·공백, 카카오맵 사용 설정 확인 |
| 호출 허용 IP 제한 | 등록했다면 현재 요청의 공인 IP 확인 |
| 429 | 사용량·쿼터 확인 |
| 네트워크·timeout·파싱 오류 | try-except로 처리하고 안전한 오류 기록 |
| 지도 실패 또는 검색 0건 | 빈 맛집 목록으로 최종 리포트 계속 |
| 최종 LLM 실패 | 확보한 자료로 대체 리포트 저장, 종료 코드 1 |

키와 인증 헤더 전체를 출력하지 않습니다. 지도 정상 0건은 API 오류와 구분합니다.

## 결과 확인 및 제출

`results/`에 한국 표준시의 **실행 날짜·시각과 입력 여행 날짜**를 포함한 JSON·Markdown 한 쌍을 저장합니다. 화면에 표시된 경로에서 확인합니다.

- **JSON:** 파싱된 추천 `recommendation`, 맛집 `restaurants`, 오류 `errors`, 날짜·처리 상태
- **Markdown:** 추천 지역·이유, 날씨, 행사·축제 후보, 맛집, 오전/오후/저녁 일정, errors

날씨는 일반적인 계절 정보이고 행사는 후보이므로 실제 예보와 일정은 방문 전에 확인합니다.

`results/`는 Git에서 제외됩니다. **실제 실행 JSON·Markdown 한 쌍을 별도 첨부하거나, 비밀 값 확인 후 examples/에 복사해 제출**합니다. 과제 원문에는 스크린샷 제출 조건이 없으며 별도 제출 양식이 있다면 따릅니다.

## 테스트

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

테스트는 외부 API를 mock으로 대체합니다. 실제 API 실행과 구분하고, 제출 전 실제 키로 실행하여 결과 파일과 필수 리포트 항목을 확인합니다.
