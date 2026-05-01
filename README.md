# Job Radar (개인 취업 준비용)

로그인 없이 **공개 채용공고 검색 결과 페이지**를 읽어서,
공고 제목/회사명/링크/출처를 수집하고 CSV로 저장하는 1차 버전입니다.

> 대상 사이트: 사람인, 잡코리아, 원티드  
> 제외: LinkedIn

---

## 1) 기능

- Selenium으로 검색 결과 페이지 접속 (로그인 기능 없음)
- 공고 정보 추출
  - `title` (공고 제목)
  - `company` (회사명)
  - `link` (공고 링크)
  - `source` (사람인/잡코리아/원티드)
- 키워드 기반 점수화
  - 가점 키워드: 글로벌, 브랜드마케팅, 디지털마케팅, 이커머스, 퍼포먼스마케팅, 가전
  - 감점 키워드: 신입, 인턴, 사무보조, 영업지원, TM, 파견, 단기계약
- 결과 CSV를 `output/` 폴더에 저장

---

## 2) 사용 전 준비 (초보자용)

### A. Python 설치

- Python 3.10 이상 설치 권장
- 설치 확인:

```bash
python --version
```

### B. 프로젝트 폴더 이동

```bash
cd /workspace/job-radar
```

### C. 가상환경 생성/활성화 (권장)

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### D. 패키지 설치

```bash
pip install -r requirements.txt
```

---

## 3) 실행 방법

## 방법 1: URL을 인자로 바로 전달

```bash
python scraper.py "https://www.saramin.co.kr/zf_user/search/recruit?searchword=마케팅" "https://www.jobkorea.co.kr/Search/?stext=브랜드" "https://www.wanted.co.kr/search?query=디지털%20마케팅"
```

## 방법 2: 실행 후 URL 입력

```bash
python scraper.py
```

실행하면 프롬프트가 뜨고, URL들을 쉼표(,)로 구분해 입력하면 됩니다.

---

## 4) 결과 확인

실행이 끝나면 `output/` 폴더에 아래 형식으로 파일이 생성됩니다.

- `job_radar_YYYYMMDD_HHMMSS.csv`

CSV 컬럼:

- `source`
- `title`
- `company`
- `link`
- `score`
- `reason`

---

## 5) 운영 원칙 (중요)

- 하루 1회 수동 실행 기준
- 로그인/캡차 우회/프록시 우회 기능 없음
- 공개 페이지에서 보이는 정보만 수집
- 사이트 이용약관과 robots 정책을 직접 확인 후 사용 권장

---

## 6) 파일 구조

- `scraper.py`: 수집 및 CSV 저장 메인 스크립트
- `requirements.txt`: 필요한 Python 패키지
- `output/`: 결과 CSV 저장 폴더 (실행 시 자동 생성)

---

## 7) 타임아웃 문제 해결 팁

- 일부 검색 결과 URL은 네트워크/사이트 상태에 따라 로딩 타임아웃이 날 수 있습니다.
- 현재 스크립트는 타임아웃 URL을 자동으로 건너뛰고 다음 URL을 계속 처리합니다.
- 그래도 반복 실패하면 URL을 한 번에 여러 개 넣지 말고 **하나씩** 실행해 원인을 확인하세요.

예시:

```bash
python scraper.py "https://www.saramin.co.kr/zf_user/search/recruit?searchword=마케팅"
```
