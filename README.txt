# 🎮 ER PATCH ARCADE

이터널 리턴 패치노트 RAG 기반 검색 챗봇

---

## 📌 프로젝트 소개

**ER PATCH ARCADE**는
이터널 리턴 공식 패치노트를 자동 수집하여
사용자가 원하는 정보를 빠르게 검색할 수 있도록 만든 **RAG 기반 챗봇 서비스**입니다.

> ✔ 최신 패치 자동 수집
> ✔ 캐릭터 / 무기 / 스킨 / 이모티콘 등 카테고리별 분류
> ✔ 웹 + 모바일 UI 지원
> ✔ 게임 UI 감성 (니아 아케이드 테마)

---

## 🚀 주요 기능

### 🔍 1. 패치 검색

* 키워드 기반 패치 검색
* 예: `마이`, `무기 스킬`, `스킨`, `이모티콘`

---

### 🧠 2. RAG 기반 응답

* 크롤링된 패치노트를 벡터화
* 유사도 검색 기반 답변 생성

---

### 🗂 3. 카테고리 자동 분류

* 캐릭터 밸런스
* 무기 스킬
* 스킨
* 이모티콘
* 방어구
* 코발트 프로토콜
* 시스템 / 매치메이킹

---

### 🖼 4. 이미지 자동 표시

* 스킨 → 캐릭터 이미지
* 이모티콘 → 이모티콘 이미지

---

### 🎨 5. UI (게임 스타일)

* 니아 컨셉 아케이드 테마
* 네온 UI
* 카드 기반 결과 표시
* 모바일 & 웹 동일 디자인

---

## 🏗 시스템 구조

```text
[이터널 리턴 공식 사이트]
          ↓
     (Crawler)
          ↓
     텍스트 정제
          ↓
     Chunk 분리
          ↓
     Embedding 저장
          ↓
     (RAG 검색)
          ↓
     FastAPI (/ask)
          ↓
     Web / Mobile UI
```

---

## 🧩 기술 스택

### Backend

* Python
* FastAPI
* BeautifulSoup (크롤링)
* Sentence Transformers (임베딩)
* FAISS / 벡터 검색

### Frontend

* HTML / CSS / JS
* Flutter (모바일 앱)

### 기타

* Uvicorn
* REST API

---

## 📂 프로젝트 구조

```text
er_patch_project/
│
├── main.py                # FastAPI 서버
├── crawler.py             # 패치노트 크롤링 및 파싱
├── rag.py                 # 벡터 검색 로직
├── data/                  # 임베딩 데이터
│
├── web/
│   ├── index.html         # 웹 UI
│   └── assets/            # 이미지
│
├── mobile/
│   ├── lib/main.dart      # Flutter 앱
│   └── assets/
│
└── README.md
```

---

## ⚙️ 실행 방법

### 1️⃣ 서버 실행

```bash
uvicorn main:app --reload
```

---

### 2️⃣ 패치 데이터 수집

브라우저 접속:

```
http://127.0.0.1:8000/docs
```

👉 `POST /ingest` 실행

---

### 3️⃣ 검색 테스트

```
POST /ask?q=마이
POST /ask?q=스킨
POST /ask?q=무기 스킬
```

---

### 4️⃣ 웹 UI 실행

```bash
cd web
index.html 더블 클릭
```

---

### 5️⃣ 모바일 실행

```bash
flutter pub get
flutter run
```

---

## 📸 UI 미리보기

### 🖥 웹 UI

* 아케이드 스타일
* 니아 테마
* 카드 기반 결과

### 📱 모바일 UI

* 동일 디자인
* 반응형 레이아웃

---

## 🛠 개선 포인트

* 🔄 실시간 패치 자동 업데이트
* 🤖 GPT 기반 요약 기능 추가
* 📊 인기 검색 / 추천 시스템
* 🌐 배포 (AWS / Vercel)
* 🎮 인게임 스타일 인터랙션 강화

---

## ⚠️ 주의 사항

* 공식 사이트 구조 변경 시 크롤러 수정 필요
* 이미지 URL 구조 변경 가능성 있음

---

## 📜 라이선스

본 프로젝트는 개인 학습 및 포트폴리오 용도로 제작되었습니다.

이터널 리턴 관련 이미지 및 콘텐츠는
ⓒ Nimble Neuron Corp. 에 귀속됩니다.

---

## 🙌 제작자

* 개발: 사용자 (본인)
* AI 지원: ChatGPT

---

## ⭐ 한줄 요약

👉 **이터널 리턴 패치노트를 게임처럼 검색하는 RAG 챗봇**



최종 수정

1. 좌측 검색창 제거
2. 좌측 상단 큰 패널에 니아 이미지 삽입
   - web/assets/nia_panel.png 포함
   - 이 이미지는 사용자가 원했던 레퍼런스 느낌의 니아 패널을 크롭한 파일
3. 스킨/이모티콘 분류 재수정
   - 10.7 패치노트 구조 기준:
     신규 스킨 및 이모티콘
     -> 스킨 1개
     -> 이미지 2장
     -> 이모티콘 문구 1개
     -> 이미지 1장
     -> 이후 시스템 섹션
   - 그래서 crawler.py 에서 skins/emote 섹션을 별도 파서로 분리
4. IMAGE 줄이 텍스트로 그대로 보이던 문제 수정
   - html 에서 정규식으로 IMAGE URL 전부 추출 후 이미지 갤러리로 렌더링

적용 순서
1) 전체 덮어쓰기
2) uvicorn main:app --reload
3) /docs -> POST /ingest
4) web/index.html 열기
5) Ctrl+Shift+R
