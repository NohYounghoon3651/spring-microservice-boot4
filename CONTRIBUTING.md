# 기여 안내

이 저장소는 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』 예제를 Spring Boot 4.0.9 / Java 21로 옮긴 코드입니다. 오류 제보와 수정 제안을 환영합니다.

## 이슈

- **질문**: 학습 중 궁금한 점은 `질문` 템플릿으로 남겨 주세요. 장별 학습 이슈(#1~#23)에 댓글로 남겨도 됩니다.
- **실행 오류**: 빌드·테스트·배포가 실패하면 `실행 오류` 템플릿으로 장, 실행 방식, 명령, 로그를 함께 적어 주세요. 먼저 위키의 [자주 발생하는 문제](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/자주-발생하는-문제)를 확인해 주세요.

## 풀 리퀘스트

1. `main`에서 브랜치를 만들어 수정합니다. `main`에는 직접 push할 수 없고 PR로만 병합됩니다.
2. 고친 장에서 직접 확인합니다.
   ```bash
   cd ChapterXX
   ./gradlew build
   ./test-em-all.bash start stop      # 4장 이후 (18장 이후는 위키의 docker compose 실행 방법 참고)
   ```
3. 여러 장에 같은 코드가 반복되는 경우가 많습니다. 한 장을 고쳤다면 이후 장의 같은 파일도 함께 고쳐 주세요.
4. PR을 올리면 GitHub Actions가 모든 장의 빌드, 단위·통합 테스트, docker compose·Kafka·파티션·네이티브 구성의 전체 시스템 테스트를 실행합니다(약 1시간). **CI result** 검사가 통과해야 병합할 수 있습니다.
5. Boot 4 마이그레이션과 관련된 변경이면 해당 장의 `MIGRATION-BOOT4.md`에도 이유를 적어 주세요.

## 문서

- 위키는 `docs/wiki/`의 마크다운에서 자동으로 게시됩니다. 위키 화면에서 직접 고치지 말고 이 폴더를 수정해 주세요.
- 문서(`*.md`, `docs/`)만 바꾼 push에서는 빌드 CI가 실행되지 않습니다.

## 원본과 비교

교재 원본 코드는 `original-boot3` 브랜치에 있습니다. 장별로 바뀐 내용은 다음 명령으로 볼 수 있습니다.

```bash
git fetch origin original-boot3
git diff origin/original-boot3 origin/main -- Chapter13
```
