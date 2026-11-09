# 출처와 라이선스 (NOTICE)

이 저장소에 들어 있는 자료의 출처와 저작권, 라이선스를 정리합니다.

## 원본 예제 코드

- 『Microservices with Spring Boot and Spring Cloud』(Magnus Larsson 지음, Packt) 4판의 예제 코드입니다. 한국어판은 『스프링 부트 3와 스프링 클라우드를 활용한 마이크로서비스 구축』(마그누스 라르손 지음, 트랜스메이트 옮김, 위키북스, 2025)입니다.
- 저작권: Copyright (c) 2025 Packt
- 라이선스: MIT License ([LICENSE](LICENSE))
- 원본 코드는 [`original-boot3`](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3) 브랜치에 수정 없이 보관합니다.

## 이 저장소에서 수정·추가한 내용

- Spring Boot 4.0.9 / Java 21 / Spring Cloud 2025.1.4로의 마이그레이션, CI·자동화 설정, 위키와 학습 자료(`docs/`, `tools/`, 각 장의 `MIGRATION-BOOT4.md`·`BOOK-GUIDE.md`)
- 저작권: Copyright (c) 2026 NohYounghoon3651
- 라이선스: 원본과 같은 MIT License ([LICENSE](LICENSE))
- 수정 전후 차이는 `original-boot3`와 `main` 브랜치를 비교하면 볼 수 있습니다.

## 출판사 자료

아래 자료는 코드가 아니라 출판사의 자료입니다. 원본 예제 코드 묶음에 들어 있던 것을 **수정하지 않고** 그대로 두었으며, 저작권은 각 출판사에 있습니다.

| 자료 | 내용 | 저작권 |
|---|---|---|
| `README.md`의 도서 정보·책 소개 부분 | 한국어판 도서 정보와 소개 글 | 위키북스 |
| `cover.jpg` | 한국어판 표지 | 위키북스 |

원본 예제 코드에는 원서 각 장의 질문에 대한 해답(`Assessments.pdf`, Packt)도 들어 있었지만, 출판사 자료라서 이 저장소에서는 뺐습니다. 해답은 교재(원서는 [Packt 도서 페이지](https://www.packtpub.com/product/microservices-with-spring-boot-and-spring-cloud/9781805801276), 한국어판은 [위키북스 도서 페이지](https://wikibook.co.kr/spring-microservice/))에서 확인하세요.

권리자가 요청하면 위 표의 자료도 바로 내리겠습니다. [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues)나 저장소 소유자에게 알려 주세요.

## 교재 본문

이 저장소에는 교재 본문이 들어 있지 않습니다. 위키와 각 장의 `BOOK-GUIDE.md`는 교재의 쪽 번호로 위치만 가리키고, 설명은 새로 썼습니다. 책 내용은 교재를 구입해서 보세요.

## 컨테이너 이미지

GitHub Container Registry(`ghcr.io/nohyounghoon3651/spring-microservice-boot4/*`)에 배포하는 이미지에는 `/licenses/LICENSE`와 `/licenses/NOTICE.md`가 들어 있고, OCI 라벨 `org.opencontainers.image.licenses=MIT`와 소스 저장소 주소가 붙어 있습니다(v1.1.1부터). 이미지에 포함된 서드파티 라이브러리와 기본 이미지는 각자의 라이선스를 따릅니다.
