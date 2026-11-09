![cover](cover.jpg)

> **스프링 부트 4.0.9 / 자바 21 버전 코드**
>
> [![Build all chapters](https://github.com/NohYounghoon3651/spring-microservice-boot4/actions/workflows/build.yml/badge.svg)](https://github.com/NohYounghoon3651/spring-microservice-boot4/actions/workflows/build.yml)
> [![Kubernetes](https://github.com/NohYounghoon3651/spring-microservice-boot4/actions/workflows/kubernetes.yml/badge.svg)](https://github.com/NohYounghoon3651/spring-microservice-boot4/actions/workflows/kubernetes.yml)
>
> 이 저장소의 예제 코드는 교재(자바 24, 스프링 부트 3.5, 스프링 클라우드 2025.0)에서 **자바 21, 스프링 부트 4.0.9, 스프링 클라우드 2025.1.4**로 옮겨져 있습니다. 교재 본문과 코드가 다른 부분은 위키의 [마이그레이션 요약](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/Spring-Boot-4-마이그레이션-요약)을 참고하세요. 전체 변경 내용은 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)를, 장별 변경 파일은 각 `ChapterXX/MIGRATION-BOOT4.md`를 참고하세요. 모든 장의 빌드·테스트, docker compose·Kafka·네이티브 구성의 전체 시스템 테스트, 쿠버네티스(Istio 포함) 배포 테스트가 GitHub Actions에서 자동으로 실행됩니다.
>
> **학습 가이드**: [위키](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki)에서 장별 학습 목표·실행 방법·복습 질문을 보고, [장별 학습 이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues?q=is%3Aissue+label%3A학습+sort%3Acreated-asc)(#1 = 1장 … #23 = 23장)의 하위 이슈(개념 · 코드 분석 · 실습 · 심화)를 닫아 가며 진도를 관리하세요. 부별 진행률은 [마일스톤](https://github.com/NohYounghoon3651/spring-microservice-boot4/milestones)에서, 장·부별 이슈는 라벨 `chXX` · `1부`/`2부`/`3부`로 볼 수 있습니다. 질문과 토론은 [Discussions](https://github.com/NohYounghoon3651/spring-microservice-boot4/discussions)에서 받습니다.
>
> **설치 없이 실습**: [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/NohYounghoon3651/spring-microservice-boot4) (JDK 21 · Docker · kubectl · Helm · minikube 포함). 장별 서비스 이미지는 릴리스마다 [GitHub Packages](https://github.com/NohYounghoon3651?tab=packages&repo_name=spring-microservice-boot4)에 `ghcr.io/nohyounghoon3651/spring-microservice-boot4/chXX-<서비스>:<버전>`으로 올라갑니다. 자세한 내용은 위키의 [Codespaces와 컨테이너 이미지](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/Codespaces와-컨테이너-이미지)를 참고하세요.
>
> **원본과 비교**: 교재 원본 코드(Boot 3.5 / Java 24)는 [`original-boot3`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3) 브랜치에 있습니다. [전체 변경 비교](https://github.com/NohYounghoon3651/spring-microservice-boot4/compare/original-boot3...boot4-migration-diff)는 파일이 많아 웹에서는 일부만 보이므로, 장별로는 `git diff origin/original-boot3 origin/main -- Chapter13`처럼 확인하세요. 기여 방법은 [CONTRIBUTING.md](CONTRIBUTING.md)를 참고하세요.
>
> **손코딩 워크북**: 3장부터 23장까지 모든 예제 코드를 단계별로 직접 쳐서 완성하는 [워크북](workbook/README.md)이 있습니다. 3장은 처음부터, 4장부터는 이전 장 결과에서 바뀌는 부분만 칩니다.
>
> **영문 3판으로 공부한다면**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판(Spring Boot 3.0 / Java 17)을 보며 실습할 때 이 저장소 코드와 다르게 읽어야 할 곳을 각 장 폴더의 `BOOK-GUIDE.md`(예: [`Chapter11/BOOK-GUIDE.md`](Chapter11/BOOK-GUIDE.md))에 쪽 번호와 함께 정리했습니다. 1·2·8·21·22장처럼 예제 코드가 없는 장도 폴더에 가이드만 있습니다.
>
> **출처와 라이선스**: 예제 코드의 원저작자는 마그누스 라르손(Magnus Larsson)과 Packt이며 MIT 라이선스로 공개되어 있습니다. 이 저장소는 그 코드를 Spring Boot 4로 수정하고 학습 자료를 더한 것으로, 같은 MIT 라이선스를 따릅니다. 아래 도서 정보·책 소개와 `cover.jpg`는 원본 예제 코드에 들어 있던 위키북스 자료를 그대로 둔 것입니다. 원본에 있던 연습문제 해답(`Assessments.pdf`, Packt)은 출판사 자료라 이 저장소에서 뺐습니다. 자세한 내용은 [NOTICE.md](NOTICE.md)와 [LICENSE](LICENSE)를 보세요.
>
> **보안 점검**: CodeQL이 19개 프로젝트의 자바 코드 전체를 분석하고, Dependabot이 의존성 취약점을 알립니다. Spring Boot는 4.0.9로 고정하고, 취약한 라이브러리만 장별 `settings.gradle`의 `securityPatches`에서 패치 버전으로 올립니다([처리 기준](CONTRIBUTING.md#codeql-알림-처리-기준)).
>
> **브랜치**: Git Flow를 따릅니다. `main`은 릴리스된 검증본(태그 `vX.Y.Z`), `develop`은 통합 브랜치이며, 작업은 `feature/*`·`fix/*`·`docs/*` 브랜치(`<유형>/<이슈번호>-<설명>`)에서 `develop`으로 PR을 올립니다. 커밋 메시지와 PR 제목은 깃모지 규칙(`✨ feat: …`, `🐛 fix: …`, `📝 docs: …`)을 따릅니다. 실습은 `main` 또는 [최신 릴리스](https://github.com/NohYounghoon3651/spring-microservice-boot4/releases)로 하세요.

# 스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축
### 스프링 클라우드, 이스티오, 쿠버네티스를 활용한 견고하고 확장성 있는 마이크로서비스 구축과 배포

- **마그누스 라르손** 지음 | **트랜스메이트** 옮김
- ISBN: 9791158396299
- 판형: 188\*240\*30mm
- 42,000원 | 2025년 11월 12일 발행 | 744쪽
- [책 홈페이지](https://wikibook.co.kr/spring-microservice/)
- [도서 미리보기](http://www.yes24.com/Product/Viewer/Preview/162329192)
- [도서 관련 문의](https://wikibook.co.kr/support/contact/)

---

**단계별로 배우는 견고하고 확장성 있는 마이크로서비스 구축과 배포!**

이 책에서는 실용적인 접근 방식을 채택해 간단한 마이크로서비스부터 시작해 복잡한 분산 애플리케이션을 구축하는 과정을 단계적으로 진행한다. 그 과정에서 마이크로서비스 구축에 필수적인 기능들을 학습하고 쿠버네티스와 이스티오를 이용해 마이크로서비스를 배포하는 방법을 익힐 수 있다.

4차 개정판인 이 책에서는 자바 24, 스프링 부트 3.5, 스프링 클라우드 2025를 사용한다. 코드 예제가 전체적으로 업데이트됐으며, 사용 중단된 API는 대체되어 최신 정보를 제공한다. 스프링의 AOT 모듈, 관찰 가능성, 분산 추적, 쿠버네티스 패키징을 위한 헬름에 대한 지식을 배울 수 있다.

실습에서는 도커 컴포즈를 사용해 데이터베이스 및 메시징 서비스와 함께 마이크로서비스를 실행하는 것으로 시작해 이스티오를 사용해 쿠버네티스에 마이크로서비스를 배포한다. 또한 데이터 영속성, 복원력, 반응형 마이크로서비스, OpenAPI를 활용한 API 문서화를 비롯해 넷플릭스 유레카를 활용한 서비스 디스커버리, 스프링 클라우드 게이트웨이를 활용한 에지 서버 구축, 프로메테우스, 그라나파, EFK 스택을 활용한 모니터링을 배운다.

이 책을 마치고 나면 스프링 부트와 스프링 클라우드를 활용해 견고하고 확장성 있는 마이크로서비스를 구축할 수 있을 것이다.

**★ 이 책에서 다루는 내용 ★**

- 스프링 부트를 활용한 반응형 마이크로서비스 구축
- 스프링 클라우드를 활용한 탄력적이고 확장 가능한 마이크로서비스 개발
- OAuth 및 스프링 시큐리티를 활용한 API 보호
- 도커를 이용한 개발, 테스트, 생산 환경 간의 격차 해소
- 쿠버네티스를 이용한 마이크로서비스 배포 및 관리
- 이스티오를 적용해 보안, 관찰 가능성, 트래픽 관리를 개선
- JUnit, 테스트 컨테이너, 그레이들, bash를 이용한 마이크로서비스 테스트 자동화
- 스프링 AOT 및 GraalVM을 이용한 마이크로서비스의 네이티브 컴파일
- 마이크로미터 트레이싱을 활용한 분산 추적

---
 
 ## 구입처
 
 - [예스24](https://www.yes24.com/product/goods/162329192)
 - [교보문고](https://product.kyobobook.co.kr/detail/S000218324078)
 - [알라딘](https://www.aladin.co.kr/shop/wproduct.aspx?ItemId=375713687)
 - [쿠팡](https://www.coupang.com/vp/products/9160967843?itemId=26983857867)
