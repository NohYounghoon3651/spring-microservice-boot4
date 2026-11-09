# 손코딩 워크북

『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』의 예제를 **처음부터 직접 쳐서** 완성하는 워크북입니다.
코드는 이 저장소의 Spring Boot 4.0.9 / Java 21 버전입니다.

## 진행 방식

1. **3장은 처음부터** 만듭니다. `spring init`으로 골격을 만든 뒤 파일을 하나씩 칩니다.
2. **4장부터는 이전 장 결과를 복사해서** 그 장에서 바뀌는 부분만 칩니다. 이전 장을 끝내지 못했다면 저장소의 완성 코드를 복사해 시작해도 됩니다.
3. 각 장은 **단계**(프로젝트 단위)로 나뉘어 있습니다. 단계마다
   - **새 파일**은 전체 코드를,
   - **수정할 파일**은 바뀐 부분(diff)을 보여 줍니다. 완성된 파일 전체는 펼쳐 볼 수 있습니다.
   - **지울 파일**은 `rm` 명령으로 안내합니다.
4. 단계가 끝나면 **중간 확인**으로 컴파일만 해 보고, 장 끝의 **확인하기**에서 테스트와 전체 시스템 실행으로 검증합니다.

복사·붙여넣기보다 **직접 치는 것**을 권합니다. 치면서 클래스 이름, 애너테이션, 설정 키를 손에 익히는 것이 이 워크북의 목적입니다.
막히면 저장소의 완성 코드와 `diff -r`로 비교해 보세요.

## 준비

- JDK 21, Docker(Compose v2), Git, `curl`, `jq` — 15장부터 `kubectl`, `minikube`, `helm`, 18장부터 `istioctl` 1.31.4
- 설치 방법: 위키 [실습 환경 준비](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/실습-환경-준비)와 교재 21·22장 대응 가이드
- 이 저장소를 클론해 두세요. Gradle 래퍼(`gradlew`, `gradle/wrapper`)와 바이너리 파일은 저장소에서 복사합니다.

```bash
git clone https://github.com/NohYounghoon3651/spring-microservice-boot4.git ~/spring-microservice-boot4     # <저장소>
mkdir -p ~/my-work                                  # 직접 치는 작업 폴더
```

워크북 명령에 나오는 `<저장소>`는 클론한 폴더(`~/spring-microservice-boot4`)를 뜻합니다.

## 장별 워크북

| 장 | 만들거나 바꾸는 파일 | 직접 칠 코드(줄) |
|---|---:|---:|
| [3장 협업 마이크로서비스 생성](Chapter03.md) | 45 | 약 1,499 |
| [4장 도커를 사용한 배포](Chapter04.md) | 10 | 약 166 |
| [5장 OpenAPI를 사용한 API 문서화](Chapter05.md) | 8 | 약 156 |
| [6장 영속성 추가](Chapter06.md) | 52 | 약 2,139 |
| [7장 반응형 마이크로서비스 개발](Chapter07.md) | 46 | 약 1,854 |
| [9장 넷플릭스 유레카를 사용한 서비스 검색](Chapter09.md) | 27 | 약 270 |
| [10장 스프링 클라우드 게이트웨이를 에지 서버로 사용](Chapter10.md) | 20 | 약 268 |
| [11장 API 접근 보안](Chapter11.md) | 44 | 약 1,196 |
| [12장 구성 중앙화](Chapter12.md) | 55 | 약 967 |
| [13장 Resilience4j를 사용한 탄력성 개선](Chapter13.md) | 9 | 약 192 |
| [14장 분산 추적](Chapter14.md) | 35 | 약 218 |
| [15장 쿠버네티스 소개](Chapter15.md) | 7 | 약 34 |
| [16장 쿠버네티스에 마이크로서비스 배포](Chapter16.md) | 118 | 약 1,641 |
| [17장 쿠버네티스 기능으로 시스템 환경 단순화](Chapter17.md) | 63 | 약 1,112 |
| [18장 서비스 메시를 사용한 관찰 가능성 및 관리 편의성 향상](Chapter18.md) | 94 | 약 1,391 |
| [19장 EFK 스택을 사용한 중앙 집중식 로깅](Chapter19.md) | 10 | 약 347 |
| [20장 마이크로서비스 모니터링](Chapter20.md) | 23 | 약 116 |
| [23장 네이티브 컴파일 자바 마이크로서비스](Chapter23.md) | 63 | 약 1,017 |

예제 코드가 없는 장([1장](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter01/BOOK-GUIDE.md), [2장](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter02/BOOK-GUIDE.md), [8장](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter08/BOOK-GUIDE.md), [21장](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter21/BOOK-GUIDE.md), [22장](https://github.com/NohYounghoon3651/spring-microservice-boot4/blob/main/Chapter22/BOOK-GUIDE.md))은 교재와 교재 대응 가이드로 공부하세요.

## 교재와 함께 보기

- 워크북은 **무엇을 치는지**에 집중합니다. **왜 그렇게 하는지**는 교재 본문을 보세요. 각 장 머리에 영문 3판 쪽 범위와 [교재 대응 가이드](../Chapter03/BOOK-GUIDE.md) 링크가 있습니다.
- 교재(Spring Boot 3.x)와 코드가 다른 곳은 각 장의 `BOOK-GUIDE.md`와 `MIGRATION-BOOT4.md`에 정리돼 있습니다.

## 워크북 갱신

워크북의 코드는 `tools/workbook/build.py`가 각 장 폴더에서 만들어 내고, `tools/workbook/verify.py`가 워크북만으로 각 장을 다시 만들어 저장소 코드와 똑같은지 확인합니다. 코드가 바뀌면 CI가 워크북도 최신인지 검사합니다.
