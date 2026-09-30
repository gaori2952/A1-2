# 국내 여행 추천 CLI

여행 날짜를 입력하면 Gemini가 국내 지역 1곳을 구조화된 JSON으로 추천하고, Kakao Local 키워드 검색으로 음식점 후보를 찾은 뒤 최종 Markdown 여행 리포트를 만듭니다.

## 데이터 흐름

`날짜 검증 → Gemini 추천 JSON → recommended_city 맛집 검색 → Gemini 리포트 → JSON/Markdown 저장`

Kakao 검색은 최대 5곳의 음식점 후보를 가져옵니다. 검색이 실패해도 빈 목록과 오류를 기록하고 최종 LLM 단계로 진행합니다. 정상적인 검색 결과가 0건인 경우는 API 실패와 구분합니다. 실제 예보, 확정 축제 일정, 평점, 영업시간, 가격이나 이동시간을 조회하지 않습니다.

## 요구 사항

- Python 3.11 이상
- Gemini API 키와 계정에서 사용 가능한 모델 ID
- Kakao REST API 키

의존성은 `requirements.txt`에 있습니다. 개발 테스트에는 `requirements-dev.txt`를 사용합니다. API 모델 ID와 사용량 제한은 계정 및 시점에 따라 다르므로 직접 확인해야 합니다.

## 설치 및 설정

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

`.env`에 다음 값을 설정하세요. 환경변수는 `.env` 값보다 우선합니다.

```dotenv
GEMINI_API_KEY=실제_Gemini_API_키
GEMINI_MODEL=계정에서_사용_가능한_모델_ID
KAKAO_REST_API_KEY=실제_Kakao_REST_API_키
```

키가 하나라도 없거나 모델 ID가 비어 있으면 외부 API를 호출하기 전에 종료합니다. `.env`는 Git에 올리지 마세요.

## 실행

```powershell
python main.py -date "2026-10-15"
python main.py --help
```

`-date`는 필수입니다. `--date`도 사용할 수 있으며 날짜는 `YYYY-MM-DD` 형식과 실제 달력 날짜를 모두 검사합니다. 잘못된 입력은 종료 코드 2, 설정/치명적 API/저장 실패는 1, 지도 경고가 있더라도 리포트 저장이 성공하면 0을 반환합니다. 최종 LLM 실패 시 대체 리포트를 `fallback` 상태로 저장하고 종료 코드 1을 반환합니다.

## 결과

프로젝트 루트의 `results/`에 실행 시각(대한민국 표준시)과 여행 날짜를 포함한 동일 stem의 `.json`, `.md` 파일을 생성합니다. JSON에는 추천, 정규화된 맛집, 검색·리포트 상태, 안전한 오류 요약이 담깁니다. 추천 JSON의 유효성 오류는 최대 한 번 재요청합니다. 장소 데이터가 없으면 Markdown 맛집 섹션에 `데이터 없음`을 표시하며, 최종 맛집 목록은 코드가 검증된 검색 결과만으로 렌더링합니다.

`results/`는 `.gitignore` 대상입니다. 제출에 결과가 필요하면 실제 키로 실행한 결과에서 비밀값이 없는지 확인한 뒤 별도 제출 위치에 포함하세요. 이 저장소를 준비할 때 실제 자격 증명이나 외부 API를 사용하지 않았으므로, 모의 테스트 결과를 실제 API 실행 결과로 취급하면 안 됩니다.

## 테스트

```powershell
python -m pytest
```

테스트는 날짜 경계, 잘못된 추천 스키마의 1회 재시도, Kakao 응답 정규화 및 0건, 지도 실패 후 최종 LLM 진행, 리포트의 필수 일정과 맛집 일치를 mock으로 확인합니다. 실제 API 통합 실행은 별도로 수행해야 합니다.

## 파일 구조

```text
main.py
travel/
  cli.py          CLI 및 날짜 인자
  config.py       환경 설정
  errors.py       안전한 오류 데이터
  llm.py          Gemini REST 요청과 추천 재시도
  places.py       Kakao 검색과 장소 정규화
  pipeline.py     전체 단계 실행
  prompts.py      추천/리포트 프롬프트
  report.py       리포트 검증·보완·대체 생성
  storage.py      결과 파일 저장
tests/
```

Gemini는 POST 요청 본문으로 프롬프트와 구조화 출력 설정을 전달하고, Kakao Local은 GET 요청의 쿼리 파라미터로 지역명과 음식점 카테고리를 전달합니다. API 키는 코드나 결과에 저장하지 않으며, 외부 예외의 원문도 로그에 남기지 않습니다.
