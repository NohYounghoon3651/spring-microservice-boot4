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

# 3. 릴리스: develop에서 release 브랜치를 만들고 main으로 PR → 병합 후 태그
git switch -c release/1.1.0 develop
git push -u origin release/1.1.0      # main 대상 PR, 병합 후 v1.1.0 태그와 릴리스 노트
# 병합 뒤 main을 develop에 역병합하는 PR을 연다
```

PR 제목과 커밋 메시지는 `<유형>: <요약>` 형식을 권장합니다(`feat`, `fix`, `docs`, `ci`, `chore`, `release`).

## CI

- PR을 올리면 GitHub Actions가 모든 장의 빌드, 단위·통합 테스트, docker compose·Kafka·파티션·네이티브 구성의 전체 시스템 테스트를 실행합니다(약 1시간). 문서만 바꾼 PR은 빌드를 건너뜁니다.
- **CI result** 검사가 통과해야 병합합니다.
- `main`으로 가는 PR(release·hotfix)은 쿠버네티스 검증(헬름, minikube, 이스티오)도 함께 실행합니다.
- `main`과 `develop`은 매주 월요일 새벽 자동으로 다시 검증됩니다.

## 이슈

- **장별 학습 이슈**: #1~#23. 각 장은 `개념` · `코드 분석` · `실습` · `심화` 하위 이슈로 나뉘어 있습니다.
- **라벨**: 장 `ch01`~`ch23`, 부 `1부`·`2부`·`3부`, 유형 `학습`·`하위 학습`·`개념`·`코드 분석`·`실습`·`심화`, 작업 `작업`·`질문`·`실행 오류`
- **질문**: `질문` 템플릿으로 남기거나, 해당 장 학습 이슈에 댓글로 남겨 주세요.
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

## 원본과 비교

교재 원본 코드는 `original-boot3` 브랜치에 있습니다.

```bash
git fetch origin original-boot3
git diff origin/original-boot3 origin/develop -- Chapter13
```
