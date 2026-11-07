# 기여 안내

이 저장소는 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 예제를 Spring Boot 4.0.9 / Java 21로 옮긴 코드입니다. 오류 제보와 수정 제안을 환영합니다.

## 브랜치 전략 (Git Flow)

| 브랜치 | 용도 | 만드는 곳 → 병합하는 곳 |
|---|---|---|
| `main` | 릴리스된 검증본. 커밋마다 `vX.Y.Z` 태그 | `release/*`, `hotfix/*`에서만 병합 |
| `develop` | 다음 릴리스를 모으는 통합 브랜치 (PR의 기본 대상) | `feature/*`, `docs/*`, `fix/*`에서 병합 |
| `feature/<이슈번호>-<설명>` | 기능·자동화 작업 | `develop` → `develop` |
| `fix/<이슈번호>-<설명>` | 릴리스 전 버그 수정 | `develop` → `develop` |
| `docs/<이슈번호>-<설명>` | 문서·위키 작업 | `develop` → `develop` |
| `release/<버전>` | 릴리스 준비 (버전·문서 정리, 전체 검증) | `develop` → `main` (태그) → `develop`에 역병합 |
| `hotfix/<버전>` | 릴리스된 버전의 긴급 수정 | `main` → `main` (태그) → `develop`에 역병합 |
| `original-boot3` | 교재 원본 코드 (변경하지 않음) | — |

작업 흐름:

```bash
# 1. 이슈를 만들고 번호를 확인한 뒤 develop에서 브랜치를 만든다
git switch develop && git pull
git switch -c feature/42-add-something

# 2. 커밋하고 push한 뒤 develop을 대상으로 PR을 연다 (본문에 "Closes #42")
git push -u origin feature/42-add-something

# 3. 릴리스: develop에서 release 브랜치를 만들고 main으로 PR → 병합 후 릴리스(태그) 발행
#    릴리스를 발행하면 컨테이너 이미지가 게시되고, 위키가 main 기준으로 다시 게시된다
git switch -c release/1.1.0 develop
git push -u origin release/1.1.0      # main 대상 PR, 병합 후 v1.1.0 태그와 릴리스 노트
# 병합 뒤 main을 develop에 역병합하는 PR을 연다
```

`develop`은 기본 브랜치가 아니어서, PR 본문의 `Closes #번호`는 `develop`에 병합될 때 이슈를 자동으로 닫지 않습니다(`main`에 릴리스될 때 닫힘). 병합 후 이슈에 PR을 연결해 직접 닫아 주세요.

## 커밋 메시지와 PR 제목 (깃모지)

커밋 메시지와 PR 제목은 `<깃모지> <유형>: <요약>` 형식으로 씁니다. 요약은 한국어로, 관련 이슈가 있으면 끝에 `(#번호)`를 붙입니다.

| 깃모지 | 유형 | 쓰는 경우 |
|---|---|---|
| ✨ | `feat` | 새 기능, 새 예제 |
| 🐛 | `fix` | 버그 수정 |
| 🚑️ | `fix` | `hotfix/*`의 긴급 수정 |
| 📝 | `docs` | 문서, 위키, README |
| ♻️ | `refactor` | 동작을 바꾸지 않는 코드 정리 |
| ✅ | `test` | 테스트 추가·수정 |
| 👷 | `ci` | GitHub Actions 워크플로 추가·수정 |
| 💚 | `ci` | 깨진 CI 고치기 |
| ⬆️ | `chore` | 의존성 버전 올리기 (Dependabot 포함) |
| 🔧 | `chore` | 설정 파일 (`application.yml`, `docker-compose*.yml`, 헬름 values) |
| 🐳 | `chore` | Dockerfile, 컨테이너 이미지 |
| 🔥 | `chore` | 코드·파일 삭제 |
| 🔖 | `release` | 릴리스, 버전 태그 |
| 🔀 | `merge` | 브랜치 병합 (역병합 포함) |
| ⏪️ | `revert` | 되돌리기 |

예: `✨ feat: 13장 product 서비스에 서킷 브레이커 설정 추가 (#120)`, `🐛 fix: 18장 Istio 테스트의 메시지 대기 시간 보강`, `🔖 release: v1.1.0`

깃모지는 [gitmoji.dev](https://gitmoji.dev)의 목록을 따릅니다. 표에 없는 경우도 그 목록에서 고르면 됩니다. 이미 push된 과거 커밋은 해시가 바뀌므로 고쳐 쓰지 않습니다.

## CI와 자동화

- PR을 올리면 모든 장의 빌드, 단위·통합 테스트, 전체 시스템 테스트가 실행됩니다(약 1시간). 문서만 바꾼 PR은 빌드를 건너뜁니다.
- **CI result** 검사가 통과해야 병합합니다.
- `main`으로 가는 PR(`release/*`·`hotfix/*`)은 쿠버네티스 검증도 함께 실행합니다. `release/*`·`hotfix/*` 브랜치는 이 PR로 검증하므로 push 때 따로 실행하지 않습니다.

| 워크플로 | 언제 | 하는 일 |
|---|---|---|
| Build all chapters (`build.yml`) | PR, `develop`·`main` push, 매주 월요일 03:00 KST | 19개 프로젝트 빌드·테스트, docker compose·Kafka·파티션·네이티브 전체 시스템 테스트, 위키 생성 결과 확인(**Wiki up to date**). 결과는 **CI result** 하나로 모음 |
| Kubernetes (`kubernetes.yml`) | `main` 대상 PR, `main` push, 매주 월요일 05:00 KST | 헬름 렌더링·스키마 검증, minikube(16·17장), minikube + Istio(18·19·20·23장) 배포 후 테스트 |
| CodeQL (`codeql.yml`) | `main`·`develop` PR·push, 매주 수요일 04:30 KST | 19개 프로젝트를 장별로 따로 분석하는 자바 코드 보안 분석 |
| Dependency submission (`dependency-submission.yml`) | `main` push | 장별 Gradle 의존성을 의존성 그래프에 등록. Dependabot 취약점 알림이 이 그래프를 사용 |
| Codespaces devcontainer (`devcontainer.yml`) | `.devcontainer/` 변경 | Codespaces 컨테이너가 만들어지고 4장이 빌드되는지 확인 |
| Label pull requests (`labeler.yml`) | PR | 바뀐 파일에 따라 `chXX`, `N부`, `작업`, `documentation` 라벨 부착 |
| Publish wiki (`wiki.yml`) | `main`의 `docs/wiki/` 변경 | 위키에 게시 (커밋 `📝 docs: update wiki …`) |
| Publish container images (`images.yml`) | 릴리스 발행 | 장별 서비스 이미지를 `ghcr.io/nohyounghoon3651/spring-microservice-boot4/chXX-<서비스>:<버전>`·`latest`로 게시 |
| Dependabot (`dependabot.yml`) | 매월 | `develop` 대상 PR: Actions(`⬆️ ci(deps)`), Gradle 패치 버전(`⬆️ chore(deps)`). 취약점 알림은 Security 탭 |

## CodeQL 알림 처리 기준

[Code scanning](https://github.com/NohYounghoon3651/spring-microservice-boot4/security/code-scanning)에 알림이 뜨면 아래 기준으로 처리합니다. CodeQL은 장마다 따로 분석하므로 같은 코드가 여러 장에 있으면 장마다 알림이 뜹니다. 고칠 때는 같은 코드가 있는 모든 장을 함께 고칩니다.

| 알림 | 처리 | 이유 |
|---|---|---|
| Disabled Spring CSRF protection (게이트웨이, 유레카, 컨피그 서버, `TestSecurityConfig`) | 분석에서 제외 (`codeql.yml`의 `query-filters`) | 브라우저 세션 없이 HTTP Basic·OAuth2 토큰으로 서비스끼리 호출하므로 CSRF가 해당되지 않음. 켜면 유레카 등록, `/encrypt`·`/decrypt` 실습이 동작하지 않음 |
| Deprecated method invocation (`withDefaultPasswordEncoder`) | 분석에서 제외 | 교재의 데모 사용자. 코드 주석에 운영 사용 금지 명시. 컴파일러의 사용 중단 경고는 빌드에서 0건으로 관리 |
| Constant interface anti-pattern (`MySqlTestBase`) | 분석에서 제외 | Testcontainers 컨테이너를 테스트끼리 공유하는 베이스 클래스 |
| 위험한 암호화 알고리즘, `@Override` 누락 등 동작 변화 없이 고칠 수 있는 것 | 코드 수정 | 표준 표기·어노테이션으로 교재 의도를 바꾸지 않고 해결 |

새로운 종류의 알림은 이슈로 남겨 판단한 뒤 이 표에 추가해 주세요. 교재 의도라서 모든 장에서 그대로 둘 규칙이면 `codeql.yml`의 `query-filters`에 추가하고, 한두 곳뿐이면 알림 화면에서 사유와 함께 닫습니다.

## 이슈

- **장별 학습 이슈**: #1~#23. 각 장은 `개념` · `코드 분석` · `실습` · `심화` 하위 이슈로 나뉘어 있습니다.
- **라벨**: 장 `ch01`~`ch23`, 부 `1부`·`2부`·`3부`, 유형 `학습`·`하위 학습`·`개념`·`코드 분석`·`실습`·`심화`, 작업 `작업`·`질문`·`실행 오류`
- **질문·토론**: 학습 중 궁금한 점, 실습 경험 공유, 개선 아이디어는 [Discussions](https://github.com/NohYounghoon3651/spring-microservice-boot4/discussions)에 남겨 주세요. 특정 장의 내용이면 해당 장 학습 이슈에 댓글로 남겨도 됩니다. `질문` 이슈 템플릿도 그대로 쓸 수 있습니다.
- **실행 오류**: `실행 오류` 템플릿으로 장, 실행 방식, 명령, 로그를 함께 적어 주세요. 먼저 위키의 [자주 발생하는 문제](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/자주-발생하는-문제)를 확인해 주세요.

## 코드 수정 시 주의

1. 고친 장에서 직접 확인합니다.
   ```bash
   cd ChapterXX
   ./gradlew build
   ./test-em-all.bash start stop      # 4장 이후 (18장 이후는 위키의 docker compose 실행 방법 참고)
   ```
2. 여러 장에 같은 코드가 반복되는 경우가 많습니다. 한 장을 고쳤다면 이후 장의 같은 파일도 함께 고쳐 주세요.
3. Boot 4 마이그레이션과 관련된 변경이면 해당 장의 `MIGRATION-BOOT4.md`에도 이유를 적어 주세요.

## 문서

- 위키는 `docs/wiki/`의 마크다운에서 자동으로 게시됩니다(`main`에 반영될 때). 위키 화면에서 직접 고치지 말고 이 폴더를 수정해 주세요.
- 장별 페이지, Home, 사이드바, 푸터는 [`tools/wiki/learning.py`](tools/wiki)가 코드에서 만듭니다(이전 장 대비 변경 파일·의존성 등). 코드를 고친 PR은 다음을 실행해 결과를 함께 커밋하세요. CI의 **Wiki up to date** 검사가 확인합니다.
  ```bash
  python3 tools/wiki/learning.py
  ```
- 직접 쓰는 페이지(실습 환경 준비, 마이그레이션 요약, 자주 발생하는 문제, 브랜치 전략, Codespaces와 컨테이너 이미지)는 스크립트가 덮어쓰지 않으니 `docs/wiki/`에서 바로 고치면 됩니다. 장별 학습 목표·복습 질문 같은 문구는 `tools/wiki/learning.py`·`review_qa.py`를 고칩니다.

## 원본과 비교

교재 원본 코드는 `original-boot3` 브랜치에 있습니다.

```bash
git fetch origin original-boot3
git diff origin/original-boot3 origin/main -- Chapter13
```
