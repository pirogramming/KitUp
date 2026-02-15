# 🏀 KITUP

개발 기간 : 2026.01.26 - 2026.02.19

<br>

> **개발자 팀 프로젝트가 끝까지 완주되도록 돕는 레벨·열정 기반 협업 매칭 플랫폼**

기존 팀매칭 서비스가 팀을 연결하는 데에만 집중했다면, **KITUP**은 팀이 **끝까지 완주할 수 있는 구조와 기준**을 제공합니다.

사용자의 **실력 레벨**과 **열정 레벨**을 기준으로 팀을 매칭하고, 프로젝트 진행 과정에서 **활동·기록·회고가 자연스럽게 남도록 설계**되었습니다.

<br>

### **KITUP url : https://kitup.duckdns.org**

<br>
<br>

# 📌 목차
- [❓ 왜 KITUP인가?](#-왜-kitup인가)
- [🎯 주요 기능](#-주요-기능)
- [🏗 프로젝트 구조](#-프로젝트-구조)
- [🛠 기술 스택](#-기술-스택)
- [🎯 대상 이용자](#-대상-이용자)
- [💪🏻 팀원 구성](#-팀원-구성)
- [🔗 협업 및 문서](#-협업-및-문서)

<br>

# ❓ 왜 KITUP인가?

기존 팀매칭 서비스는 팀을 **'연결'해주는 역할**에만 집중하며, 팀 프로젝트가 실패하는 핵심 원인을 해결하지 못합니다.

<div align="center">

| 문제 | 설명 |
|---|---|
| 🎯 **실력·목표 불일치** | 기술 스택 중심 매칭으로 실제 협업 가능 수준 판단이 어려움 |
| 🚪 **책임 구조 부재** | 무임승차, 중도 이탈, 소수 인원의 과도한 부담 |
| 📝 **기록이 남지 않음** | 협업 중 고민, 역할, 기여도가 구조적으로 저장되지 않음 |
| 🔒 **높은 진입장벽** | 입문자는 팀플 경험과 진행 방법 부족으로 참여 자체가 어려움 |

</div>

**KITUP**은 이 모든 문제를 **구조적으로** 해결합니다.

<br>

# 🎯 주요 기능

### 1️⃣ 실력 레벨 + 열정 레벨 기반 팀 매칭
- 가입 시 **설문 기반 실력 레벨 진단** (1~4단계)
- 팀플 신청 시 **열정 레벨 측정** (주당 투자 시간, 목표 수준 기반)
- **동일/인접 레벨** 간 매칭으로 불일치 최소화
  - 같은 팀 내 열정 차이 ≤ 1
  - 같은 팀 내 실력 차이 ≤ 1
- 분야별(FE / BE / PM) 실력 레벨 분리 관리
- **인접 레벨 윈도우 분할 매칭 알고리즘** 적용

### 2️⃣ 시즌 기반 프로젝트 운영
- **팀매칭 기간** + **프로젝트 기간**
- 시즌 단위 팀 구성 및 프로젝트 관리
- 팀 프로젝트 관리 페이지 제공

### 3️⃣ 입문자 전용 팀플 가이드
- 레벨별 팀플 진행 순서 안내
- MVP 볼륨 추천, 역할 분배 가이드
- **체크리스트·미션 형식**으로 퀘스트를 깨듯 진행

### 4️⃣ 회고 및 활동 기록
- 마크다운 기반 **회고 가이드** 제공
- 프로젝트 종료 후 기록 자동 저장 → 협업 경험이 자산으로 축적

### 5️⃣ 마이페이지 및 성장 관리
- 기술 스택별 실력 레벨 표기 및 재진단
- 참여한 팀플 이력 및 상세 기록 열람
- 프로필 관리 기능

<br>

# 🏗 프로젝트 구조

```
KitUp/
├── apps/
│   ├── accounts/          # 회원 인증, 프로필, 기술 스택, 레벨 관리
│   ├── guides/            # 팀플 가이드, 미션 카드, 체크리스트
│   ├── projects/          # 시즌 관리, 팀 프로젝트 운영, 매칭 알고리즘
│   ├── reflections/       # 회고 작성, 활동 기록, 피드백
│   ├── teams/             # 팀 매칭, 팀 생성/관리
├── config/                # Django 설정
├── static/                # 정적 파일 (CSS, JS, 이미지)
├── templates/             # HTML 템플릿
```

<br>

### 📦 앱 상세

<div align="center">

| 앱 | 기능 |
|---|---|
| **accounts** | 회원가입, 로그인(allauth), 실력 레벨 진단, 기술 스택 관리, 프로필 |
| **guides** | 역할별(FE/BE/PM) 학습 미션, 팀플 가이드 카드, 체크리스트 |
| **projects** | 시즌 생성/관리, 팀매칭 기간·프로젝트 기간 설정, 팀 프로젝트, **인접 레벨 매칭 알고리즘** |
| **reflections** | 마크다운 회고 작성, GitHub 활동 기록 수집, 프로젝트 기록 저장 |
| **teams** | 열정 레벨 기반 팀 매칭, 팀원 모집·지원, 팀 관리 |

</div>

<br>

### 📄 주요 페이지

<div align="center">

| 페이지 | 설명 |
|---|---|
| **메인 페이지** | 서비스 소개 및 시즌 안내 |
| **회원가입 / 실력 레벨 진단** | 가입 후 설문 기반 실력 레벨(1~4) 측정 |
| **팀플 탐색 및 신청 / 열정 레벨 진단** | 팀 찾기, 신청 시 열정 레벨 설문 |
| **팀 프로젝트 관리** | 프로젝트 개요, 팀원 정보, 팀플 가이드 |
| **회고 / 기록** | 회고 작성, GitHub 커밋 수집, 기록 저장 |
| **마이페이지** | 프로필 편집, 실력 레벨 확인/재진단, 팀플 이력 |

</div>

<br>

# 🛠 기술 스택

### Stacks
<div align="center">
  
| 구분 | Stack  |
| :------: |  :------: |
| **FE** | ![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white) ![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) |
| **BE** | ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white) |
| **SERVER** | ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white) ![AWS](https://img.shields.io/badge/AWS-%23FF9900.svg?style=for-the-badge&logo=amazon-aws&logoColor=white) |

</div>

<br>

### Tools
<div align="center">
  
![Figma](https://img.shields.io/badge/figma-%23F24E1E.svg?style=for-the-badge&logo=figma&logoColor=white) ![Visual Studio Code](https://img.shields.io/badge/Visual%20Studio%20Code-0078d7.svg?style=for-the-badge&logo=visual-studio-code&logoColor=white)
</div>

### Collaboration
<div align="center">

![Notion](https://img.shields.io/badge/Notion-%23000000.svg?style=for-the-badge&logo=notion&logoColor=white) ![Discord](https://img.shields.io/badge/Discord-%235865F2.svg?style=for-the-badge&logo=discord&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)

</div>

<br>

# 🎯 대상 이용자

<div align="center">

| 대상 | 설명 |
|---|---|
| 🌱 **개발 입문자** | 팀플 경험이 없거나 부족한 사용자 |
| 🔄 **재도전자** | 사이드 프로젝트를 하고 싶지만 팀이 자주 무너졌던 사용자 |
| 📋 **기록자** | 협업 경험을 체계적으로 남기고 싶은 사용자 |
| 🎯 **목표 지향형** | 명확한 기간과 목표를 가지고 완주하고 싶은 사용자 |

</div>

<br>

# 💪🏻 팀원 구성

<div align="center">

| **성유리** | **장민지** | **김민하** | **이수종** | **이형주** |
| :------: |  :------: | :------: | :------: | :------: |
| [<img src="https://github.com/user-attachments/assets/1783348c-9d5b-444b-92c9-4394712e8498" height=200 width=150> <br/> @bimvocado](https://github.com/bimvocado)  | [<img src="https://github.com/user-attachments/assets/511cb16c-48dd-48e7-8514-12483c01c294" height=200 width=150> <br/> @plumbestie](https://github.com/plumbestie)  | [<img src="https://github.com/user-attachments/assets/36d84e47-c0a0-4f10-9c94-07ac0ecded7e" height=200 width=150> <br/> @knana6](https://github.com/knana6) | [<img src="https://github.com/user-attachments/assets/eed0e554-27d4-4093-9653-1d168c8aa238" height=200 width=150> <br/> @issuejong](https://github.com/issuejong) | [<img src="https://github.com/user-attachments/assets/c5677a38-b42f-46ee-b374-cfa3bb88d673" height=200 width=150> <br/> @Tonyjoo11](https://github.com/Tonyjoo11) |
| PM / BE |  FE | FE | BE | BE |

</div>

<br>

# 📚 핵심 알고리즘: 인접 레벨 윈도우 분할 매칭

KITUP의 팀 매칭은 **열정·실력 레벨 차이를 최소화**하도록 설계되었습니다.

### 알고리즘 특징
- **O(n log n)** 시간복잡도 (정렬 병목)
- **Greedy 접근**: 높은 열정/실력 그룹부터 우선 배정
- **2-Phase Fallback**: 강한 제약(1차) → 약한 제약(2차)
- **Deterministic**: 실행할 때마다 동일한 결과

### 제약 조건
```python
# 팀 구성 제약
- 한 팀 내 열정 차이 ≤ 1
- 같은 역할 내 실력 차이 ≤ 1
- preferred_role 100% 일치
```

### 매칭 프로세스
```
1. 역할별 분류 (PM / FE / BE)
   ↓
2. 열정 인접 그룹 (P3-4, P2-3, P1-2)
   ↓
3. 실력 인접 그룹 (Lv3-4, Lv2-3, Lv1-2)
   ↓
4. 팀 생성 (5명씩)
   ↓
5. 2차 완화 매칭 (미배정 인원)
```

**결과**: 테스트 30명 기준 6팀 생성, **조건 충족률 100%** ✅

<br>

## 📊 프로젝트 통계

- **총 코드 라인**: ~15,000 LOC
- **앱 개수**: 5개 (accounts, guides, projects, reflections, teams)
- **모델 수**: 20+
- **API 엔드포인트**: 50+
<br>

---

<div align="center">

**© 2026 KITUP. All rights reserved.**

</div>
