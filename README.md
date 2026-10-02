# 국내 여행 추천 CLI — Gemini와 Kakao API 연결하기

여행 날짜를 입력하면 **Gemini가 국내 여행지 1곳을 추천하고, Kakao Local이 그 지역의 음식점을 검색하며, Gemini가 두 결과를 조합해 여행 리포트를 만드는 Python 프로그램**입니다.

이번 미션의 핵심은 여러 API의 데이터를 연결하는 것입니다. 첫 번째 API의 결과에서 `recommended_city`를 꺼내 두 번째 API의 입력으로 사용하고, 마지막에는 추천 정보와 검색 결과를 함께 전달합니다.

## 1. 프로그램을 설명하는 순서

발표하거나 코드를 설명할 때 아래 순서로 이야기하면 됩니다.

> 사용자가 여행 날짜를 입력하면 먼저 날짜와 API 설정을 확인합니다.  
> Gemini에 날짜를 보내 지역, 계절 날씨, 행사 후보, 추천 이유를 JSON으로 받습니다.  
> JSON을 검증한 뒤 recommended_city 값을 Kakao 맛집 검색에 사용합니다.  
> 추천 JSON과 실제 검색한 맛집 목록을 다시 Gemini에 보내 Markdown 리포트를 만듭니다.  
> 마지막으로 추천·맛집·오류 정보를 JSON에, 최종 리포트를 Markdown에 저장합니다.

```text
python main.py -date "2026-10-15"
          │
          ▼
날짜 형식·실제 날짜·필수 설정 확인
          │
          ▼
Gemini POST → 추천 JSON 생성 → 파싱·검증
          │
          └─ recommended_city: "강릉"
                       │
                       ▼
Kakao GET → query="강릉 맛집" → 음식점 최대 5곳
                       │
                       ▼
추천 JSON + 맛집 목록 → Gemini POST → Markdown 리포트
                       │
                       ▼
results/에 JSON + Markdown 저장, 경로 출력
```

날씨는 실제 예보가 아닌 일반적인 계절 정보이고, 행사는 일정 확인이 필요한 후보입니다. 이 과제에서는 구조화된 출력과 API 간 연결이 핵심입니다.

## 2. 설치와 API 키 설정

과제의 환경 기준은 Python 3.10 이상이며, 이 프로젝트의 실행 환경은 **Python 3.11 이상을 권장**합니다.

### macOS / Linux

```bash
git clone https://github.com/gaori29-52/A1-2.git
cd A1-2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Windows PowerShell

```powershell
git clone https://github.com/gaori29-52/A1-2.git
cd A1-2
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

이미 `.env`가 있다면 복사 단계는 생략하여 기존 설정을 보존합니다. 프로젝트 루트의 `.env`에 아래 세 항목을 설정합니다. 예시 값은 자리표시자이며 실제 키가 아닙니다.

```dotenv
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
GEMINI_MODEL=YOUR_AVAILABLE_MODEL_ID
KAKAO_REST_API_KEY=YOUR_KAKAO_REST_API_KEY
```

- Gemini 키와 사용할 수 있는 모델 ID: [Google AI Studio](https://aistudio.google.com/)에서 확인
- Kakao 키: [Kakao Developers](https://developers.kakao.com/)에서 REST API 키와 API 이용 설정 확인

`GEMINI_MODEL`에는 본인 계정에서 사용할 수 있는 모델 ID를 넣습니다. 키 두 개뿐 아니라 모델 ID도 필수 설정입니다.

`.env` 대신 현재 터미널의 환경변수로 설정할 수도 있습니다.

```bash
# macOS / Linux: 현재 터미널 세션에 적용
export GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
export GEMINI_MODEL="YOUR_AVAILABLE_MODEL_ID"
export KAKAO_REST_API_KEY="YOUR_KAKAO_REST_API_KEY"
```

```powershell
# Windows PowerShell: 현재 세션에 적용
$env:GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
$env:GEMINI_MODEL="YOUR_AVAILABLE_MODEL_ID"
$env:KAKAO_REST_API_KEY="YOUR_KAKAO_REST_API_KEY"
```

`travel/config.py`가 `python-dotenv`로 설정을 읽습니다. 이미 설정된 환경변수가 `.env`보다 우선하며, 필수 값이 없으면 외부 API를 호출하기 전에 종료하고 설정 방법을 안내합니다.

### 왜 키를 코드에 직접 쓰지 않는가?

API 키는 외부 서비스 이용을 인증하는 비밀 값입니다. 코드와 분리하면 저장소를 공유할 때 키가 함께 공개되는 사고를 줄이고, 키를 교체할 때 코드를 수정할 필요가 없습니다. 무단 사용에 따른 과금과 쿼터 소진도 예방할 수 있습니다.

`.env`는 Git에서 제외하고, `.env.example`에는 설정 이름만 공유합니다. README, 로그, 결과 파일, 제출 자료에 실제 키나 인증 헤더 전체를 넣지 않습니다.

## 3. 실행 방법

프로젝트 루트에서 실행합니다.

```bash
python main.py -date "2026-10-15"
python main.py --help
```

필수 옵션은 `-date "YYYY-MM-DD"`이며 `--date`도 지원합니다. `argparse`로 옵션을 처리하고, 날짜 형식과 실제 존재하는 날짜를 모두 검증합니다.

```bash
# 입력 오류 예시: 사용법과 오류를 출력하고 종료
python main.py -date "2026/10/15"
python main.py -date "2026-02-30"
```

진행 로그는 입력·설정 확인, 추천 요청, 음식점 검색, 리포트 생성, 결과 저장의 5단계로 표시합니다. 저장이 완료되면 `JSON:`과 `REPORT:` 뒤에 파일 경로가 출력됩니다.

| 종료 코드 | 의미 |
| --- | --- |
| 0 | 추천 정보를 확보하고 최종 리포트를 생성·저장함. 장소 검색 실패나 0건이어도 리포트 생성에 성공하면 0일 수 있음 |
| 1 | 설정 오류, 추천 실패, 최종 LLM 실패로 인한 대체 리포트, 또는 처리된 저장 오류 |
| 2 | 필수 옵션 누락·잘못된 날짜 등 CLI 입력 오류 |

## 4. 핵심 개념을 코드와 연결해서 설명하기

### 4-1. REST API 요청·응답과 GET / POST

요청은 **URL, HTTP 메서드, 헤더, 입력 데이터**로 구성됩니다. 응답에는 **상태 코드, 헤더, 본문**이 있습니다. 이 프로그램은 상태 코드로 성공·인증 실패·사용량 제한을 판단하고, 응답 본문의 JSON에서 필요한 값을 꺼냅니다.

| 구분 | Gemini — `travel/llm.py` | Kakao — `travel/places.py` |
| --- | --- | --- |
| 메서드 | POST | GET |
| 목적 | 프롬프트를 보내 새 추천·리포트 생성 요청 | 조건에 맞는 기존 장소 정보 조회 |
| URL | 모델 ID가 포함된 `generateContent` 주소 | `/v2/local/search/keyword.json` |
| 인증 헤더 | `x-goog-api-key` | `Authorization: KakaoAK <키>` |
| 입력 위치 | JSON 본문의 `contents`, `generationConfig` | 쿼리 파라미터의 `query`, `category_group_code`, `size` |
| 응답 활용 | 응답 JSON에서 생성 텍스트 추출 | 응답 JSON의 `documents` 목록 추출 |

**설명할 때:** “GET은 조회 조건을 보내 기존 데이터를 검색하고, POST는 본문에 프롬프트와 설정을 담아 생성 작업을 요청합니다. POST 자체가 키를 보호하는 것은 아니므로 인증 값은 안전하게 관리해야 합니다.”

### 4-2. 왜 LLM의 추천을 JSON으로 받는가?

자유로운 문장에서 지역명을 추측하면 다음 API에 잘못된 값을 전달할 수 있습니다. 정해진 키를 가진 JSON으로 받으면 `recommendation["recommended_city"]`처럼 필요한 값을 명확히 꺼낼 수 있습니다.

아래는 구조 설명용 예시이며 실제 API 실행 결과가 아닙니다.

```json
{
  "recommended_city": "강릉",
  "weather": "가을에는 비교적 선선하지만 해안 바람에 대비하는 것이 좋습니다.",
  "events": ["가을 지역 문화 행사 후보 — 해당 연도 일정 확인 필요"],
  "reason": "해안 산책과 지역 문화 공간을 함께 즐길 수 있습니다. 선선한 시기에 여유로운 하루 여행을 계획하기 좋습니다."
}
```

| 필드 | 요구 타입·조건 | 구현 방식 |
| --- | --- | --- |
| `recommended_city` | 문자열, 국내 지역 1곳 | 프롬프트로 국내 지역 요청, 비어 있지 않은 문자열 검증 |
| `weather` | 문자열, 일반적 날씨 요약 | 프롬프트로 계절 정보 요청, 문자열 검증 |
| `events` | 문자열 배열, 1~3개 | 배열 길이와 각 문자열을 코드로 검증 |
| `reason` | 문자열, 추천 근거 2~4문장 | 문장 수는 프롬프트로 요청하며 코드는 비어 있지 않은 문자열인지 검증 |

`travel/prompts.py`에서 JSON 출력과 스키마를 요청하고, `travel/validation.py`에서 `json.loads()`로 파싱한 뒤 키와 타입을 검증합니다. 누락 키·추가 키·빈 문자열을 거부하고 앞뒤 공백을 제거합니다.

파싱이나 검증에 실패하면 문제를 담은 수정 프롬프트로 **최대 1회 재요청**합니다. 처음 요청까지 합쳐 최대 2번이며, 모든 API 오류를 자동으로 재시도하는 방식은 아닙니다.

**설명할 때:** “JSON은 두 API 사이의 데이터 약속입니다. LLM이 만든 값도 그대로 믿지 않고 검증한 다음 지도 API에 전달합니다.”

### 4-3. 추천 지역을 맛집 검색에 어떻게 연결하는가?

`travel/pipeline.py`에서 검증된 지역을 전달합니다.

```python
search_restaurants(recommendation["recommended_city"], settings)
```

`travel/places.py`는 지역에 “맛집”을 붙여 검색합니다.

```python
params = {
    "query": f"{city} 맛집",
    "category_group_code": "FD6",
    "size": 5
}
```

음식점 후보는 최대 5곳입니다. 검색 결과가 적거나 중복·잘못된 항목이 있으면 최종 목록은 5곳보다 적을 수 있습니다. API 응답을 다음 필드로 정리합니다.

| 결과 필드 | Kakao 응답에서 가져오는 값 |
| --- | --- |
| `name` | `place_name` |
| `address` | `road_address_name`, 없으면 `address_name` |
| `category` | `category_name` |
| `url` | `place_url` |
| `x`, `y` | 경도·위도를 숫자로 변환. 해석할 수 없으면 `null` |

검색된 음식점 목록은 별점이나 평가를 검증한 맛집 순위가 아닙니다. 이름·주소가 없는 항목은 제외하고, 중복은 제거합니다.

### 4-4. 최종 리포트는 어떻게 만드는가?

추천 JSON과 맛집 목록을 함께 Gemini에 보내 Markdown을 요청합니다. 이후 `travel/report.py`가 필수 섹션과 오전·오후·저녁 항목을 보완하고, 맛집 섹션을 실제 검색 목록으로 구성하며 오류 목록을 붙입니다.

리포트에는 다음 항목이 들어갑니다.

- 추천 지역과 이유
- 날씨 요약
- 행사·축제 후보
- 맛집 리스트 — 목록이 비면 `데이터 없음`
- 오전·오후·저녁의 1일 일정 제안
- `errors` — 기록된 오류가 없으면 `없음`

프롬프트는 검색 목록에 없는 식당이나 확인하지 않은 가격·영업시간 등을 만들지 않도록 요청합니다. 이 지시는 생성 내용의 사실성을 완전히 보장하는 검증은 아니므로 여행 전에 실제 정보를 확인해야 합니다.

## 5. 오류가 나면 어떻게 대응하는가?

외부 API는 키가 잘못되거나, 사용량 한도를 넘거나, 네트워크가 끊기거나, 예상과 다른 응답을 보낼 수 있습니다. API 호출·파싱 오류는 `try-except`로 처리하고, 내부 `errors` 목록에 요약을 모읍니다.

| 상황 | 프로그램의 처리 | 확인할 내용 |
| --- | --- | --- |
| 키·모델 설정 누락 | 외부 호출 전 즉시 종료, 설정 안내 | `.env` 또는 환경변수의 세 항목 |
| 인증 실패 401 / 403 | 안전한 오류 메시지 기록. 장소 API 실패면 빈 목록으로 리포트 계속 | 키 종류·값, 인증 헤더 형식, 이용 권한·설정 |
| 쿼터 제한 429 | 사용 한도 오류 기록. 장소 API 실패면 리포트 계속 | 서비스 사용량·쿼터 |
| 네트워크·시간 초과 | 연결 오류·시간 초과를 처리. 장소 API 실패면 리포트 계속 | 연결 상태·응답 지연 |
| 추천 JSON 파싱·검증 실패 | 수정 프롬프트로 1회 재요청 | JSON 문법, 필수 키, 타입 |
| 추천 재요청도 실패 | 확보 실패와 오류를 담은 대체 리포트 저장, 종료 코드 1 | 두 번의 검증 실패 원인 |
| 장소 응답 파싱 실패 | 빈 맛집 목록으로 리포트 계속 | 응답 JSON과 `documents` 구조 |
| 장소 검색 정상 0건 | `search_status: "empty"`, 맛집은 `데이터 없음`으로 진행 | 검색 결과가 없는 상태 |
| 최종 Gemini 호출 실패 | 확보한 추천·맛집 자료로 대체 리포트 저장, 종료 코드 1 | 오류 요약 |
| 결과 저장 중 처리된 오류 | 저장 오류 안내, 종료 코드 1 | 저장 경로·쓰기 권한 |

정상적인 0건 검색은 인증·네트워크 실패와 구분합니다. 0건이라는 이유만으로 오류를 추가하지 않으며 `errors`는 빈 배열일 수 있습니다.

오류 기록 형식의 예시는 다음과 같습니다. 실제 키나 응답 전체를 기록하지 않습니다.

```json
{
  "stage": "places",
  "code": "HTTP_401",
  "message": "장소 API 인증에 실패했습니다. REST API 키와 이용 설정을 확인하세요.",
  "attempt": 1,
  "recovered": true
}
```

여기서 `recovered: true`는 API 인증을 고쳤다는 뜻이 아니라, 해당 오류가 있어도 대체 처리로 다음 단계를 진행했다는 뜻입니다.

**설명할 때:** “장소 검색은 실패해도 추천 정보가 있으므로 리포트를 계속 만들 수 있습니다. JSON 파싱 실패는 형식 수정으로 해결할 가능성이 있어 한 번만 재요청합니다.”

## 6. 결과 파일 확인과 제출

프로젝트의 `results/` 폴더는 실행 시 생성됩니다. 한국 표준시의 실행 날짜·시각과 입력한 여행 날짜를 파일명에 사용합니다.

```text
results/
├── <실행날짜>_<시각>_<마이크로초>_<여행날짜>.json
└── <실행날짜>_<시각>_<마이크로초>_<여행날짜>.md
```

### JSON: 프로그램이 사용한 데이터

JSON에는 최소한 아래 세 가지가 들어갑니다.

- `recommendation`: 파싱·검증한 1차 추천 JSON
- `restaurants`: 정리한 맛집 검색 결과 목록, 0건이면 `[]`
- `errors`: 오류 요약 배열, 오류가 없으면 `[]`

추가로 여행 날짜, 실행 시각, API 제공자, 검색 상태와 리포트 상태를 저장합니다. 여기서 원본 데이터 JSON은 **파싱한 추천과 정리한 장소 목록을 담은 결과 데이터**이며 HTTP 응답 전체를 그대로 보관한 파일은 아닙니다. 추천에 실패한 대체 결과에서는 `recommendation`이 `null`일 수 있습니다.

### Markdown: 사람이 읽는 여행 리포트

화면에 출력된 `REPORT:` 경로의 파일을 열어 추천·날씨·행사·맛집·일정·errors가 있는지 확인합니다. `report_status: "fallback"`이면 정상 생성된 리포트 대신 대체 리포트가 저장된 상태입니다.

### 제출 전 확인

- 실제 키로 실행하여 JSON과 Markdown 한 쌍을 확보합니다.
- JSON에 추천, 맛집 목록, `errors`가 있는지 확인합니다.
- Markdown에 필수 항목과 오전·오후·저녁 일정이 있는지 확인합니다.
- 실제 키·인증 헤더가 제출 자료에 없는지 확인합니다.
- `results/`는 Git에서 제외되므로 결과 파일은 별도로 첨부하거나, 확인 후 `examples/`에 복사하여 제출합니다.

과제 원문에는 스크린샷 제출 조건이 없으므로 별도 제출 양식이 있다면 그 양식을 따릅니다.

## 7. 요구사항과 구현 위치

| 과제 요구사항 | 구현 위치·확인 방법 |
| --- | --- |
| argparse, 필수 `-date`, 날짜 검증 | `travel/cli.py`, `travel/validation.py` |
| LLM 제공자 1개 | `travel/llm.py`의 Gemini 호출 |
| 장소 제공자 1개 | `travel/places.py`의 Kakao Local 호출 |
| 추천 JSON 4개 필드 | `travel/prompts.py`의 스키마·프롬프트, `travel/validation.py`의 검증 |
| 추천 지역 → 맛집 검색 연결 | `travel/pipeline.py`의 `recommended_city` 전달 |
| 음식점 최대 5곳과 최소 필드 | `travel/places.py`의 검색·정규화 |
| 추천 JSON + 맛집 → 최종 Markdown | `travel/prompts.py`, `travel/report.py` |
| 검색 0건·장소 API 실패 시 계속 | `travel/pipeline.py`, `travel/report.py` |
| 추천 JSON 오류 재요청 최대 1회 | `travel/llm.py`의 `request_recommendation()` |
| errors 목록·리포트 오류 섹션 | `travel/errors.py`, `travel/pipeline.py`, `travel/report.py` |
| .env·환경변수와 키 누락 안내 | `travel/config.py`, `main.py`, `.gitignore` |
| results/에 실행 시각 기준 저장 | `travel/storage.py` |
| 진행 로그·저장 경로 안내 | `travel/pipeline.py` |

선택 보너스인 복수 지역 추천과 결과 캐싱은 현재 구현하지 않았습니다.

## 8. 코드 구조와 테스트

```text
A1-2/
├── main.py                 # CLI → 설정 확인 → 전체 실행
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt        # requests, python-dotenv
├── requirements-dev.txt    # 실행 의존성 + pytest
├── travel/
│   ├── __init__.py
│   ├── cli.py              # argparse
│   ├── config.py           # 설정 로딩
│   ├── validation.py       # 날짜·추천 JSON 검증
│   ├── prompts.py          # 추천 스키마·리포트 프롬프트
│   ├── llm.py              # Gemini 요청·텍스트 추출·재요청
│   ├── places.py           # Kakao 검색·필드 정리
│   ├── pipeline.py         # 단계 연결·오류 누적
│   ├── report.py           # 리포트 보완·대체 리포트
│   ├── storage.py          # JSON·Markdown 저장
│   └── errors.py           # 공통 오류·기록 형식
├── tests/
│   ├── test_cli.py
│   ├── test_validation.py
│   ├── test_places.py
│   └── test_pipeline.py
└── results/                # 실행 시 생성, Git에서 제외
```

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

테스트는 외부 API를 mock으로 대체하여 날짜 검증, 추천 검증·재요청, 장소 결과 처리, 오류 이후 진행과 리포트 구성을 확인합니다. mock 테스트 통과만으로 실제 키·권한·모델 이용 가능 여부가 확인되지는 않으므로 실제 API 실행 결과도 별도로 확인합니다.

## 9. 설명을 마무리할 때 확인할 네 가지

1. **요청·응답:** URL·메서드·헤더·입력을 보내고, 상태 코드와 JSON 본문을 확인한다.
2. **API 연결:** 추천 JSON을 검증한 뒤 `recommended_city`를 장소 검색에 전달한다.
3. **오류 대응:** 인증·쿼터·네트워크·파싱 오류를 구분하고, 장소 실패는 계속 진행하며 추천 형식 오류는 한 번만 재요청한다.
4. **키 관리:** 비밀 값을 코드와 분리해 공유 사고를 줄이고, 코드 수정 없이 키를 교체한다.
