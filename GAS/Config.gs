/**
 * ===================================================================
 * _Config.gs - 잡코리아 제안수락 자동화 설정
 * ===================================================================
 * 모든 설정값을 한 곳에서 관리한다.
 * 테스트 완료 후 TARGET_SHEET_NAME을 'RAW'로 변경하면 운영 전환 가능.
 * ===================================================================
 */

// ───────── 스프레드시트 (작업 대상) ─────────
const SPREADSHEET_ID = '1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU';
/** 테스트 완료 후 'RAW'로 변경할 것 */
const TARGET_SHEET_NAME = 'RAW';
const LEGEND_SHEET_NAME = '범례';

const SHEET_URLS = {
  'RAW': 'https://docs.google.com/spreadsheets/d/1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU/edit?gid=0#gid=0',
  'TEST': 'https://docs.google.com/spreadsheets/d/1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU/edit?gid=1698379406#gid=1698379406'
};

// ───────── 타겟 DB 스프레드시트 (회원기준정보) ─────────
const MEMBER_DB_SPREADSHEET_ID = '1DJMKrL9924RIIYegcCVcC4FTQkkeE_BO78C4IbaO2wU';
const MEMBER_DB_SHEET_NAME = '회원기준정보';

// ───────── 이메일 ─────────
const EMAIL_SENDER_NAME = '크몽 엔터프라이즈';
const EMAIL_SENDER_ADDRESS = 'alpha@kmong.com';
const RESUME_TEMPLATE_URL = 'https://drive.google.com/uc?export=download&id=1qktziD9bO_pjKC2KfZe7Y0g90d_lKx9j';

// ───────── Slack ─────────
const SLACK_WEBHOOK_URL = 'SLACK_WEBHOOK_URL';

// ───────── NHN Cloud SMS ─────────
const SMS_API_BASE_URL = 'https://api-sms.cloud.toast.com/sms/v3.0/appKeys';

/**
 * 범례 닉네임 → 스크립트 속성 키 접두사 매핑
 */
const MANAGER_NICKNAME_TO_PREFIX = {
  'Terry': 'TERRY',
  'Jess': 'JESS',
  'Kun': 'KUN',
  'Anita': 'ANITA',
  'Alpha': 'ALPHA'
};

// ───────── 상태 마커 ─────────
const PRIVATE_MARKER = '비공개';
const SENT_MARKER = '발송완료';
const SYNC_COMPLETE_MARKER = '입력완료';
const SYNC_SKIPPED_MARKER = '미입력';

// ───────── 컬럼명 (헤더 기반 매핑용) ─────────
const COL = {
  MANAGER: '담당자',
  NAME: '이름',
  GENDER: '성별',
  AGE: '나이',
  EDUCATION: '최종학력',
  EXPERIENCE: '총경력',
  RESUME_URL: '이력서URL',
  PHONE: '휴대전화번호',
  EMAIL: '이메일',
  ATTACHMENT_1: '첨부파일1',
  ATTACHMENT_2: '첨부파일2',
  ATTACHMENT_3: '첨부파일3',
  PROPOSAL_URL: '제안URL',
  POSITION: '제안포지션',
  TASK_DESC: '수행업무',
  PREFERRED: '우대사항',
  PROPOSAL_DATE: '제안일자',
  RESUME_FILE_URL: '이력서파일URL',
  SMS_STATUS: '문자안내',
  EMAIL_STATUS: '이메일안내',
  SLACK_STATUS: '슬랙안내',
  SHEET_STATUS: '시트입력'
};

// ───────── 범례 컬럼명 ─────────
const LEGEND_COL = {
  NICKNAME: '매니저_닉네임',
  NAME: '매니저_이름',
  DISPLAY_NAME: '매니저_발송용 이름',
  PHONE: '매니저_연락처',
  EMAIL: '매니저_이메일',
  SLACK_ID: '매니저_슬랙ID',
  SMS_ENABLED: '문자발송',
  EMAIL_ENABLED: '이메일발송',
  SLACK_ENABLED: '슬랙발송'
};
