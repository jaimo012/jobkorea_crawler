# ☁️ Oracle Cloud VM 생성 및 상세 세팅 가이드 (Jobkorea-Bot)

이 문서는 2026년 3월 17일 수행된 오라클 클라우드 인프라 구축 과정을 상세히 기록합니다.

---

## 1. 인스턴스(VM) 생성 단계
오라클 클라우드 콘솔에서 서버의 기초 뼈대를 잡는 과정입니다.

1.  **메뉴 진입**: 오라클 클라우드 홈에서 **[인스턴스 생성 (Create Instance)]** 버튼을 클릭합니다.
2.  **이름 설정**: 인스턴스 이름을 `jobkorea-bot`으로 지정합니다.
3.  **이미지 및 셰이프 (OS 선택)**:
    * **[Edit]** 버튼을 눌러 이미지(OS)를 **Ubuntu 20.04**로 선택합니다.
4.  **네트워킹 설정**:
    * 기본 가상 클라우드 네트워크(VCN)와 서브넷 생성을 수락합니다.
5.  **SSH 키 추가 (매우 중요)**:
    * **[전용 키 저장 (Download Private Key)]** 버튼을 눌러서 `ssh-key.key` 파일을 내 컴퓨터에 다운로드합니다. 이 파일이 없으면 서버 접속이 불가능합니다.
6.  **생성**: 맨 아래 **[Create]** 버튼을 눌러 생성을 시작합니다.

---

## 2. 공인 IP(Public IP) 수동 할당 및 네트워크 세팅
인스턴스 생성 직후에는 내부용 사설 IP(`10.0.0.101`)만 할당되어 외부 접속이 불가능했습니다. 이를 해결한 과정입니다.

1.  **VNIC 상세 페이지 진입**: 인스턴스 상세 정보 화면 하단의 **[Attached VNICs]** 항목에서 파란색 링크인 **[Jobkorea-Bot]**을 클릭합니다.
2.  **IP 관리 탭 선택**: 상단 탭 메뉴 중 **[IP Administration]**을 클릭합니다.
3.  **IP 수정**: 목록에 나타난 사설 IP(`10.0.0.101`) 우측의 점 3개(`...`) 메뉴를 눌러 **[Edit]**을 선택합니다.
4.  **공용 IP 할당**:
    * `Public IP type` 항목에서 **[Ephemeral public IP (임시 공용 IP)]**를 체크합니다.
    * 맨 아래 **[Update]** 버튼을 눌러 저장합니다.
5.  **확인**: 이제 **Public IP address** 항목에 `158.179.162.168` 같은 외부 접속용 진짜 주소가 표시됩니다.

---

## 3. 서버 접속 및 초기 환경 구축 (SSH & CMD)
내 컴퓨터(Windows)에서 서버에 접속하여 필요한 소프트웨어를 설치하는 단계입니다.

1.  **SSH 접속 명령어**: 내 컴퓨터의 `ssh-key.key` 파일 경로를 포함하여 접속합니다.
    ```bash
    ssh -i "C:\Users\jaimo\OneDrive\Desktop\개발자원\오라클\ssh-key.key" ubuntu@158.179.162.168
    ```
2.  **시스템 업데이트 및 필수 도구 설치**:
    ```bash
    sudo apt update
    sudo apt install git -y
    sudo apt install -y python3-pip
    sudo apt install -y tesseract-ocr tesseract-ocr-eng  # OCR 도구
    ```
3.  **크롬 브라우저 설치**: 서버용(Headless) 크롬을 수동 설치합니다.
    ```bash
    wget [https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb](https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb)
    sudo apt install -y ./google-chrome-stable_current_amd64.deb
    ```

---

## 4. 프로젝트 배포 및 트러블슈팅

1.  **코드 가져오기**: 깃허브 저장소를 복제합니다.
    ```bash
    git clone [https://github.com/jaimo012/jobkorea_crawler](https://github.com/jaimo012/jobkorea_crawler)
    cd jobkorea_crawler
    ```
2.  **OpenSSL 충돌 해결 (AttributeError 해결)**:
    * **증상**: `module 'lib' has no attribute 'X509_V_FLAG_NOTIFY_POLICY'`
    * **해결**: 낡은 시스템 부품을 지우고 최신화합니다.
    ```bash
    sudo apt-get remove -y python3-openssl
    sudo pip3 install --upgrade pyOpenSSL cryptography
    ```
3.  **파이썬 라이브러리 설치**: 프로젝트 부품을 설치합니다.
    ```bash
    pip3 install -r requirements.txt
    ```
4.  **비밀 파일 전송 (WinSCP)**:
    * 깃허브에 없는 `.env`, `google_credentials.json`, `jobkorea_cookies.pkl` 파일을 WinSCP를 통해 `~/jobkorea_crawler` 폴더로 드래그 앤 드롭 하였습니다.

---

## 5. 현재 상태 및 향후 과제
* **성능**: 봇 실행 및 시트 연동까지 확인 완료.
* **인증 이슈**: 서버 IP에서 접속 시 잡코리아가 다시 2단계 인증(`TwoFactorAuth`)을 요구하는 현상 발생.
* **조치 예정**: 로컬 세션 예열 강화 또는 서버 IP 기반 기기 인증 시도 필요.
