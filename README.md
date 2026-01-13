# Menton Web Runner (분리 버전)

## 폴더 구조
- `web/` : UI (index.html, app.js, style.css)
- `core/` : 언어 본체 (mentonlang.py)

## 로컬 실행 (간단)
브라우저에서 fetch가 동작하려면 로컬 서버가 필요합니다.

예:
```bash
python -m http.server 8000
```

그 다음:
- http://localhost:8000/web/

## GitHub Pages 추천 설정
Settings → Pages → Branch: main → Folder: `/web`
