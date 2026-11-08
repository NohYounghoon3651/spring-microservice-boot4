# 17장 교재 대응 가이드 — 쿠버네티스 기능으로 시스템 환경 단순화

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 17 "Implementing Kubernetes Features to Simplify the System Landscape" (p.439–464)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

Config Server를 ConfigMap·Secret으로, 게이트웨이를 Ingress로 바꾸고 cert-manager로 인증서를 발급하는 구조는 책과 같습니다. 바뀐 것은 MongoDB 접속 환경 변수 이름, cert-manager 설치 옵션, 테스트 접속 포트입니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Replacing the Spring Cloud Config Server (p.440–445) | Secret의 `SPRING_DATA_MONGODB_AUTHENTICATION_DATABASE`, `SPRING_DATA_MONGODB_USERNAME`, `SPRING_DATA_MONGODB_PASSWORD` | **`SPRING_MONGODB_AUTHENTICATION_DATABASE`**, **`SPRING_MONGODB_USERNAME`**, **`SPRING_MONGODB_PASSWORD`** (Boot 4의 `spring.mongodb.*` 키). `SPRING_CONFIG_LOCATION`으로 `config-repo` 파일을 읽는 방식은 같습니다 |
| Replacing the Spring Cloud Gateway (p.445–450) | Ingress, `_ingress.yaml` 템플릿, `cert-manager.io/issuer` 애너테이션 | 같습니다 |
| Ingress 컨트롤러 (p.453) | `minikube addons enable ingress` (컨트롤러 v1.5.1) | 같은 명령입니다. CI에서 설치된 컨트롤러는 v1.15.1이었습니다 |
| cert-manager 설치 (p.454) | `helm install cert-manager jetstack/cert-manager --version v1.11.0 --set installCRDs=true ...` | 버전을 고정하지 않고 최신 차트를 쓰며, CRD 옵션은 **`--set crds.enabled=true`**입니다(`installCRDs`는 폐기됨). CI 검증 버전은 v1.21.3 |
| Testing with ConfigMaps, Secrets, Ingress, cert-manager (p.452–458) | `/etc/hosts`에 `127.0.0.1 minikube.me`, `HOST=minikube.me PORT=8443 USE_K8S=true ./test-em-all.bash` | 책처럼 minikube를 `--ports=8443:443`으로 만들었다면 같습니다. 리눅스(CI)에서는 `$(minikube ip) minikube.me`를 hosts에 넣고 **`PORT=443`**으로 실행합니다 |
| 인증서 갱신 확인 (p.457) | `kubectl patch ... renewBefore` | 같습니다 |
| Verifying without Kubernetes (p.458–461) | `.env`, 컴포즈 파일의 `SPRING_DATA_MONGODB_*` | `.env`는 같고, 컴포즈 파일은 `SPRING_MONGODB_*`입니다. `COMPOSE_FILE=... ./test-em-all.bash start stop` 세 구성도 같습니다 |

## 더 보기

- 위키: [17장 쿠버네티스 기능으로 시스템 환경 단순화](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/17장-쿠버네티스-기능으로-시스템-환경-단순화)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter17)
- 학습 이슈: [#17](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/17)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
