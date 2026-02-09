# Paper Classifier Tool

논문 분류를 위한 웹 기반 도구입니다. 장면 그래프(Scene Graph) 관련 논문을 효율적으로 검토하고 데이터베이스화 할 수 있도록 설계되었습니다.

## 🌟 주요 업그레이드 내용

1.  **단일 데이터 소스 통합**: `classifications.json`을 폐지하고 모든 분류 결과를 `scene_graph_papers_minimal.csv`에 직접 저장하여 소스 데이터와 분류 정보의 일관성을 확보했습니다.
2.  **자동화된 워크플로우**: `npm start` 시 자동으로 ArXiv 메타데이터 수집, 인용 수 조회, 한국어 번역 및 PDF 정리가 수행됩니다.
3.  **크로스 플랫폼 원스텝 설정**: `npm run setup` 하나로 Windows, Mac, Linux 모든 환경에서 복잡한 설치 과정 없이 바로 시작할 수 있습니다.
4.  **스마트 내비게이션**: AI가 생성한 초안이나 아직 분류되지 않은 새 논문을 우선적으로 탐색합니다.

## 🛠 구조

```
paper_classifier/
├── backend/                    # FastAPI 백엔드
│   ├── main.py                # 메인 API 서버 및 동기화 로직
│   ├── sync_papers.py         # 백엔드 동기화 전용 스크립트
│   └── requirements.txt       # Python 의존성
├── frontend/                  # React 프론트엔드
│   ├── src/
│   │   ├── App.js            # 메인 대시보드 및 단축키 로직
│   │   └── components/       # UI 컴포넌트 (PDF 뷰어, 카테고리 트리 등)
├── data/                      # 설정 데이터
│   └── category_metadata.json # 카테고리 정의 트리
├── setup.js                   # 크로스 플랫폼 통합 설치 스크립트
├── package.json               # 통합 실행 스크립트 (Node.js)
└── README.md
```

## 🚀 빠른 시작 (Quick Start)

```bash
cd paper_classifier
npm run setup # 최초 1회
npm start # 실행
```

## 🛠 상세 설정 가이드 (수동 설치 시)

만약 `npm run setup`이 작동하지 않는 경우 아래 단계를 따르세요.

#### 1. 백엔드 설정 (FastAPI)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 2. 프런트엔드 설정 (React)

```bash
cd ../frontend
npm install
```

## 📂 데이터 관리 (Single Source of Truth)

- **입력/출력**: `csvs/scene_graph_papers_minimal.csv`
  - 분류 결과는 이 CSV 파일의 `category`, `subcategory`, `source` 필드에 즉시 저장됩니다.
  - `source` 필드가 `manual`이 아닌 논문들(ai_generated, uncategorized)이 우선적으로 화면에 나타납니다.
- **카테고리**: `data/category_metadata.json`
  - UI에서 추가하거나 수정한 카테고리 정보가 영구 저장됩니다.

## ⌨️ 단축키

- **Ctrl + S**: 현재 분류 저장 및 다음 미분류 논문으로 이동
- **Ctrl + N**: 현재 논문 건너뛰기
- **방향키/버튼**: 이전/다음 논문으로 자유롭게 이동 가능

## ❓ 문제 해결

### PDF가 보이지 않아요

- PDF 파일이 `pdfs/` 폴더에 있는지 확인하세요.
- 파일명이 ArXiv ID 형식이거나 논문 번호로 되어 있어야 합니다. (자동 동기화 사용 시 알아서 정리됩니다.)

### 인용 횟수가 0으로 나와요

- 배포 직후의 논문은 OpenAlex API에 등록되기까지 시간이 걸릴 수 있습니다.
- API 조회 실패 시 기본값인 0으로 표시됩니다.

### 한국어 번역이 안 돼요

- `deep-translator` 라이브러리가 설치되어 있는지 확인하세요. (`npm run setup` 시 자동 설치됨)
- 인터넷 연결 상태를 확인하세요.

---

**Note**: 본 도구는 연구 목적으로 개발되었으며, `csvs/` 및 `pdfs/` 폴더는 상위 디렉토리에 위치해야 합니다.
