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
