# All arXiv Scene Graph Papers Classified

Reposity for classifying all arXiv scene graph papers.  
장면 그래프(Scene Graph) 관련 arXiv 논문을 분류하기 위한 저장소입니다.

---

## 📚 Categories

Classified 35.8%(370/1034)

- [**Scene Graph**](./classified/Scene%20Graph/Scene%20Graph.md)
  - [3D Scene Graph](./classified/Scene%20Graph/Scene%20Graph-3D%20Scene%20Graph.md)
  - [Dataset/Benchmark](./classified/Scene%20Graph/Scene%20Graph-Dataset_Benchmark.md)
  - [Dynamic Scene Graph](./classified/Scene%20Graph/Scene%20Graph-Dynamic%20Scene%20Graph.md)
  - [General](./classified/Scene%20Graph/Scene%20Graph-General.md)
  - [Grounding](./classified/Scene%20Graph/Scene%20Graph-Grounding.md)
  - [Representation](./classified/Scene%20Graph/Scene%20Graph-Representation.md)
  - [Scene Graph Generation](./classified/Scene%20Graph/Scene%20Graph-Scene%20Graph%20Generation.md)
  - [Scene Graph Parsing](./classified/Scene%20Graph/Scene%20Graph-Scene%20Graph%20Parsing.md)
  - [Synthesis](./classified/Scene%20Graph/Scene%20Graph-Synthesis.md)
  - [Others](./classified/Scene%20Graph/Scene%20Graph-Others.md)
- [**Robotics**](./classified/Robotics/Robotics.md)
  - [General](./classified/Robotics/Robotics-General.md)
  - [Manipulation](./classified/Robotics/Robotics-Manipulation.md)
  - [Navigation](./classified/Robotics/Robotics-Navigation.md)
  - [Robotic Perception](./classified/Robotics/Robotics-Robotic%20Perception.md)
  - [Task-planning](./classified/Robotics/Robotics-Task-planning.md)
- [**Reasoning**](./classified/Reasoning/Reasoning.md)
  - [Captioning](./classified/Reasoning/Reasoning-Captioning.md)
  - [Grounding](./classified/Reasoning/Reasoning-Grounding.md)
  - [Prediction](./classified/Reasoning/Reasoning-Prediction.md)
  - [Reasoning](./classified/Reasoning/Reasoning-Reasoning.md)
  - [Relationship](./classified/Reasoning/Reasoning-Relationship.md)
  - [Retrieval](./classified/Reasoning/Reasoning-Retrieval.md)
  - [Scene Understanding](./classified/Reasoning/Reasoning-Scene%20Understanding.md)
  - [VQA](./classified/Reasoning/Reasoning-VQA.md)
  - [Others](./classified/Reasoning/Reasoning-Others.md)
- [**Others**](./classified/Others/Others.md)
  - [AR/VR](./classified/Others/Others-AR_VR.md)
  - [Active Learning](./classified/Others/Others-Active%20Learning.md)
  - [Autonomous Driving](./classified/Others/Others-Autonomous%20Driving.md)
  - [Medical](./classified/Others/Others-Medical.md)
  - [Other Applications](./classified/Others/Others-Other%20Applications.md)
  - [Weakly Related](./classified/Others/Others-Weakly%20Related.md)
  - [Not Related](./classified/Others/Others-Not%20Related.md)
  - [Uncategorized](./classified/Others/Others-Uncategorized.md)


---

## 🌟 paper_classifier

논문 초록(Abstract)과 PDF 원본을 읽고 카테고리별로 분류할 수 있는 웹 기반 도구입니다.

- 모든 분류 결과는 `scene_graph_papers_minimal.csv`에 저장
- 한글 번역은 google 번역 서비스를 이용.

#### 📋 필요 조건 (Requirements)

- **Node.js**: v16.14.0 이상 (v18+ 권장)
- **Python**: v3.8 이상 (`python3` 명령어가 터미널에서 실행 가능해야 합니다)
- **npm**: Node.js 설치 시 함께 설치됩니다.

#### 🚀 빠른 시작 (Quick Start)

```bash
cd paper_classifier
npm run setup # 최초 1회
npm start # 실행
```

#### [🛠 상세 설정 가이드](./paper_classifier/README.md) (수동 설치 시)

#### 📂 새 논문 추가 방법

ArXiv ID가 포함된 PDF 파일(예: `2601.12345v1.pdf`)을 `pdfs/` 폴더에 넣고, `npm start`를 실행합니다.
