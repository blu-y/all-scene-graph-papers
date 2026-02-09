# All arXiv Scene Graph Papers Classified

장면 그래프(Scene Graph) 관련 ArXiv 논문을 분류하기 위한 저장소입니다.
논문 초록(Abstract)과 PDF 원본을 읽고 카테고리별로 분류할 수 있는 웹 기반 도구입니다.

---

## 🌟 주요 기능

- **단일 데이터 소스**: 모든 분류 결과가 `scene_graph_papers_minimal.csv`에 직접 저장되어 데이터 일관성을 유지합니다.
- **자동 동기화 (Auto-Sync)**: `pdfs/` 폴더에 새 논문을 넣기만 하면 자동으로 정보를 등록합니다.
  - ArXiv ID 자동 추출 및 파일명 정리 (`2301.1234.pdf`)
  - ArXiv API를 통한 제목, 초록, 저자 정보 수집
  - **OpenAlex API** 연동을 통한 실시간 인용 횟수(`citations`) 업데이트
  - **Google 번역 서비스**를 활용한 한글 초록 자동 생성
- **스마트 내비게이션**: 분류가 완료되지 않은 논문(`ai_generated`, `uncategorized`)을 우선적으로 찾아 보여줍니다.
- **크로스 플랫폼 지원**: Windows, Mac, Linux 환경에서 동일하게 작동합니다.

---

## 📋 필요 조건 (Requirements)

- **Node.js**: v16.14.0 이상 (v18+ 권장)
- **Python**: v3.8 이상 (`python3` 명령어가 터미널에서 실행 가능해야 합니다)
- **npm**: Node.js 설치 시 함께 설치됩니다.

---

## 🚀 빠른 시작 (Quick Start)

```bash
cd paper_classifier
npm run setup # 최초 1회
npm start # 실행
```

##### [🛠 상세 설정 가이드 (수동 설치 시)](./paper_classifier/README.md)

##### 📂 새 논문 추가 방법

ArXiv ID가 포함된 PDF 파일(예: `2601.12345v1.pdf`)을 `pdfs/` 폴더에 넣고, `npm start`를 실행합니다.

---

## 📚 Categories

- [**Scene Graph**](./classified/Scene%20Graph/Scene%20Graph.md)
  - [3D Scene Graph](./classified/Scene%20Graph/Scene%20Graph-3D%20Scene%20Graph.md)
  - [Dataset](./classified/Scene%20Graph/Scene%20Graph-Dataset.md)
  - [Dynamic Scene Graph](./classified/Scene%20Graph/Scene%20Graph-Dynamic%20Scene%20Graph.md)
  - [Representation](./classified/Scene%20Graph/Scene%20Graph-Representation.md)
  - [Scene Graph Generation](./classified/Scene%20Graph/Scene%20Graph-Scene%20Graph%20Generation.md)
  - [Scene Graph Retrieval](./classified/Scene%20Graph/Scene%20Graph-Scene%20Graph%20Retrieval.md)
  - [Survey](./classified/Scene%20Graph/Scene%20Graph-Survey.md)
  - [Synthesis](./classified/Scene%20Graph/Scene%20Graph-Synthesis.md)
  - [Others](./classified/Scene%20Graph/Scene%20Graph-Others.md)
- [**Robotics**](./classified/Robotics/Robotics.md)
  - [Manipulation](./classified/Robotics/Robotics-Manipulation.md)
  - [Navigation](./classified/Robotics/Robotics-Navigation.md)
  - [Robotic Perception](./classified/Robotics/Robotics-Robotic%20Perception.md)
  - [Task-planning](./classified/Robotics/Robotics-Task-planning.md)
- [**Reasoning**](./classified/Reasoning/Reasoning.md)
  - [Prediction](./classified/Reasoning/Reasoning-Prediction.md)
  - [Reasoning](./classified/Reasoning/Reasoning-Reasoning.md)
  - [Relationship](./classified/Reasoning/Reasoning-Relationship.md)
  - [Retrieval](./classified/Reasoning/Reasoning-Retrieval.md)
  - [VPR](./classified/Reasoning/Reasoning-VPR.md)
  - [VQA](./classified/Reasoning/Reasoning-VQA.md)
  - [Others](./classified/Reasoning/Reasoning-Others.md)
- [**Others**](./classified/Others/Others.md)
  - [Autonomous Driving](./classified/Others/Others-Autonomous%20Driving.md)
  - [Medical](./classified/Others/Others-Medical.md)
  - [Not Related](./classified/Others/Others-Not%20Related.md)
  - [Weakly Related](./classified/Others/Others-Weakly%20Related.md)
