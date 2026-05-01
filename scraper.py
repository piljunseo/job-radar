import argparse
import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Tuple
from urllib.parse import urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


UP_KEYWORDS = [
    "글로벌",
    "브랜드마케팅",
    "디지털마케팅",
    "이커머스",
    "퍼포먼스마케팅",
    "가전",
]

DOWN_KEYWORDS = [
    "신입",
    "인턴",
    "사무보조",
    "영업지원",
    "TM",
    "파견",
    "단기계약",
]

EXCLUDED_DOMAINS = {"linkedin.com", "www.linkedin.com"}


@dataclass
class JobPosting:
    source: str
    title: str
    company: str
    link: str
    score: int
    reason: str


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def score_job(title: str, company: str) -> Tuple[int, str]:
    target = f"{title} {company}".lower().replace(" ", "")
    score = 0
    reasons = []

    for word in UP_KEYWORDS:
        if word.lower().replace(" ", "") in target:
            score += 2
            reasons.append(f"+2:{word}")

    for word in DOWN_KEYWORDS:
        if word.lower().replace(" ", "") in target:
            score -= 2
            reasons.append(f"-2:{word}")

    return score, ", ".join(reasons) if reasons else "none"


def get_source(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "saramin" in host:
        return "사람인"
    if "jobkorea" in host:
        return "잡코리아"
    if "wanted" in host:
        return "원티드"
    return host


def extract_cards(driver: webdriver.Chrome, source: str) -> List[JobPosting]:
    postings: List[JobPosting] = []
    seen = set()

    # 사이트 공통/개별 후보 셀렉터들
    link_selectors = [
        "a[href*='job']",
        "a[href*='recruit']",
        "a[href*='jobs']",
        "a[href*='position']",
        "a[href*='detail']",
    ]

    anchors = []
    for selector in link_selectors:
        anchors.extend(driver.find_elements(By.CSS_SELECTOR, selector))

    for a in anchors:
        href = (a.get_attribute("href") or "").strip()
        text = normalize_text(a.text)

        if not href or not text:
            continue
        if href in seen:
            continue
        if any(domain in href for domain in EXCLUDED_DOMAINS):
            continue

        title = text

        company = ""
        parent_text = ""
        try:
            container = a.find_element(By.XPATH, "./ancestor::*[self::li or self::article or self::div][1]")
            parent_text = normalize_text(container.text)
        except Exception:
            parent_text = ""

        if parent_text:
            lines = [line.strip() for line in parent_text.split("\n") if line.strip()]
            if len(lines) >= 2:
                if title == lines[0]:
                    company = lines[1]
                else:
                    company = lines[0]

        if not company:
            company = "미확인"

        score, reason = score_job(title, company)
        postings.append(
            JobPosting(
                source=source,
                title=title,
                company=company,
                link=href,
                score=score,
                reason=reason,
            )
        )
        seen.add(href)

    return postings


def build_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1400,2000")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def validate_urls(urls: List[str]) -> List[str]:
    valid = []
    for url in urls:
        host = urlparse(url).netloc.lower()
        if not host:
            print(f"[SKIP] 잘못된 URL 형식: {url}")
            continue
        if host in EXCLUDED_DOMAINS or "linkedin" in host:
            print(f"[SKIP] LinkedIn은 대상 제외: {url}")
            continue
        if not any(k in host for k in ["saramin", "jobkorea", "wanted"]):
            print(f"[SKIP] 지원하지 않는 사이트: {url}")
            continue
        valid.append(url)
    return valid


def save_csv(rows: List[JobPosting], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = output_dir / f"job_radar_{ts}.csv"

    with out_file.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["source", "title", "company", "link", "score", "reason"])
        for r in rows:
            writer.writerow([r.source, r.title, r.company, r.link, r.score, r.reason])

    return out_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Job Radar 1차 버전 크롤러")
    parser.add_argument("urls", nargs="*", help="사람인/잡코리아/원티드 검색 결과 URL")
    parser.add_argument("--show-browser", action="store_true", help="브라우저를 화면에 표시")
    args = parser.parse_args()

    urls = args.urls
    if not urls:
        raw = input("검색 결과 URL을 쉼표(,)로 구분해 입력하세요: ").strip()
        urls = [u.strip() for u in raw.split(",") if u.strip()]

    urls = validate_urls(urls)
    if not urls:
        print("처리할 URL이 없습니다.")
        return

    driver = build_driver(headless=not args.show_browser)
    all_jobs: List[JobPosting] = []

    try:
        for url in urls:
            source = get_source(url)
            print(f"[INFO] {source} 페이지 수집 중: {url}")
            try:
                driver.get(url)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print(f"[WARN] 로딩 시간 초과: {url}")
                continue

            jobs = extract_cards(driver, source)
            print(f"[INFO] {source}에서 {len(jobs)}건 추출")
            all_jobs.extend(jobs)

    finally:
        driver.quit()

    if not all_jobs:
        print("추출된 공고가 없습니다.")
        return

    out_path = save_csv(all_jobs, Path("output"))
    print(f"[DONE] 저장 완료: {out_path}")


if __name__ == "__main__":
    main()
