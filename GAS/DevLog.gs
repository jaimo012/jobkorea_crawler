/**
 * ===================================================================
 * _DevLog.gs - 개발 히스토리
 * ===================================================================
 * 
 * 📌 프로젝트 개요
 * ─────────────────────
 * 잡코리아 제안수락 자동 안내 시스템
 * - 잡코리아에서 제안을 수락한 후보자에게 이메일/SMS/슬랙으로 안내를 자동 발송
 * - Google Sheets를 DB로 사용, GAS로 오케스트레이션
 * 
 * 
 * 📁 파일 구조
 * ─────────────────────
 * _Config.gs        - 상수, 시트 ID, API URL, 컬럼명 매핑
 * Main.gs           - 메인 오케스트레이션 (processNewAcceptances)
 * SheetService.gs   - 시트 읽기/쓰기, 범례 매칭, 행→객체 변환
 * EmailService.gs   - Gmail 발송 (HTML + Plain Text 템플릿)
 * SmsService.gs     - NHN Cloud SMS v3.0 API 호출
 * SlackService.gs   - Slack Incoming Webhook 발송
 * Utilities.gs      - 회신기한 계산 등 공통 유틸리티
 * _DevLog.gs        - 이 파일 (개발 히스토리)
 * 
 * 
 * 📝 변경 로그
 * ─────────────────────
 * [v1.0.0] 2026-03-20 - 초기 버전
 *   - 기본 흐름 구현: TEST 시트 → 이메일 → SMS → Slack → 시트 업데이트
 *   - 담당자 ↔ 범례 매니저 매칭 (매니저_이름 기준)
 *   - NHN Cloud SMS v3.0 연동 (담당자별 APP_KEY/SECRET_KEY)
 *   - Slack Incoming Webhook 연동
 *   - 회신기한 자동 계산 (다음 영업일 오전 11시)
 *   - 비공개 처리 (전화번호/이메일 = "비공개" → 해당 채널 발송 skip)
 *   - 헤더 기반 컬럼 매핑 (TEST/RAW 시트 컬럼 순서 차이 자동 대응)
 * 
 * [v1.1.0] 2026-03-23 - 타겟 DB 동기화 기능 추가
 *   - MemberSyncService.gs 신규 추가: 회원기준정보 시트에 데이터 Upsert 연동
 *   - Utilities.gs에 parseExperience 함수 추가 (총경력 문자열을 분석해 년차, 시작일 역산)
 *   - Main.gs에 Slack 발송 이후 DB 시트 동기화 로직(processDbSync) 순서 추가
 *   - 중복 발송 차단을 위해 미처리 행 조건 변경 (시트입력이 안된 건도 가져오되, 메일/문자 등은 발송완료면 Skip)
 *   - 전화번호 정규식 치환 기능 추가 (`replace(/\D/g, '')`)
 * 
 * 
 * 🔧 트러블슈팅
 * ─────────────────────
 * (아직 없음 - 테스트 진행하면서 기록 예정)
 * 
 * 
 * ⚙️ 운영 전환 체크리스트
 * ─────────────────────
 * □ _Config.gs의 TARGET_SHEET_NAME을 'TEST' → 'RAW'로 변경
 * □ RESUME_TEMPLATE_URL을 실제 개인이력카드 양식 URL로 교체
 * □ 각 매니저의 SMS 발신번호가 NHN Cloud에 등록되어 있는지 확인
 * □ 시간 기반 트리거 설정 (예: 5분 간격)
 * □ Slack Webhook URL 유효성 확인
 * 
 */
