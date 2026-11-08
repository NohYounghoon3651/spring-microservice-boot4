# 15장 교재 대응 가이드 — 쿠버네티스 소개

> **교재**: 『Microservices with Spring Boot 3 and Spring Cloud』 영문 3판, Chapter 15 "Introduction to Kubernetes" (p.373–394)  
> **이 저장소**: Spring Boot 4.0.9 · Java 21 · Spring Cloud 2025.1.4
>
> 책을 펼쳐 두고 읽다가 저장소 코드와 다른 곳을 만났을 때 무엇을 바꿔 읽으면 되는지 정리했습니다. 교재 본문은 옮기지 않았으니 설명과 그림은 책을 보세요. 쪽 번호는 책에 인쇄된 번호입니다(PDF 뷰어의 쪽 번호보다 33 작음).

> 위키북스 한국어판(4차 개정판, Spring Boot 3.5 / Java 24)으로 공부한다면 [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)가 더 직접적인 비교 자료입니다.

## 요약

쿠버네티스 개념 설명과 nginx 예제 실습(`kubernetes/first-attempts`)은 책과 같습니다. 바뀐 것은 minikube로 클러스터를 만드는 명령의 옵션과 쿠버네티스 버전입니다.

## 절별 대응

| 교재 위치 | 교재 | 이 저장소 |
|---|---|---|
| Introducing Kubernetes concepts·API objects·runtime (p.373–379) | 파드, 디플로이먼트, 서비스, 인그레스, 컨테이너 런타임 | 그대로 유효합니다 |
| Creating a Kubernetes cluster using Minikube (p.379–384) | `minikube start --profile=handson-spring-boot-cloud --kubernetes-version=v1.26.1 --ports=8080:80 --ports=8443:443 --ports=30080:30080 --ports=30443:30443` 등 | 위키와 CI는 `minikube start --driver=docker --container-runtime=docker --cpus=4 --memory=10g`처럼 **기본 프로필과 minikube 기본 쿠버네티스 버전**을 씁니다(CI 검증: minikube 1.39.0, Kubernetes 1.37.0). 책처럼 프로필과 `--ports`를 지정해도 됩니다. 버전을 고정하려면 `--kubernetes-version`에 쓰는 minikube가 지원하는 버전을 넣으세요 |
| Trying out a sample Deployment (p.384–391) | `kubectl apply -f kubernetes/first-attempts/nginx-deployment.yaml` 등 | 같습니다. 매니페스트 파일도 같습니다 |
| Managing a local Kubernetes cluster (p.391–393) | `minikube stop`, `minikube start`, `minikube delete` (`--profile` 포함) | 같습니다. 기본 프로필을 쓰면 `--profile` 옵션은 빼도 됩니다(학습 이슈 #234) |

## 참고

- `--ports` 옵션은 도커 드라이버에서 호스트의 포트를 minikube로 연결합니다. 리눅스에서는 이 옵션 없이 `$(minikube ip)`로 바로 접근할 수 있어 CI는 그 방식을 씁니다(16장 참고).
- 이 장 폴더의 `./test-em-all.bash`는 14장과 같은 시스템을 도커 컴포즈로 확인하는 용도입니다.

## 더 보기

- 위키: [15장 쿠버네티스 소개](https://github.com/NohYounghoon3651/spring-microservice-boot4/wiki/15장-쿠버네티스-소개)
- 이 장의 Boot 4 변경 내역: [MIGRATION-BOOT4.md](MIGRATION-BOOT4.md)
- 원본 코드와 비교: [`original-boot3` 브랜치](https://github.com/NohYounghoon3651/spring-microservice-boot4/tree/original-boot3/Chapter15)
- 학습 이슈: [#15](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/15)
- 이 가이드가 틀렸거나 빠진 곳을 발견하면 [이슈](https://github.com/NohYounghoon3651/spring-microservice-boot4/issues/new/choose)로 알려 주세요.
