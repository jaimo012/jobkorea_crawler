/**
 * 잡코리아 2단계 인증번호 수집기
 * Gmail에서 잡코리아 인증 메일을 읽어 구글 시트에 저장
 */

/* ── 설정 ── */
const TWOFA_CONFIG = {
  SPREADSHEET_ID: "1orsOtn-9czDxCcs6CbVJ0tjPfYDMUsg3iDyu2XBvDGU",
  SHEET_NAME: "2차인증",
  GMAIL_QUERY: 'from:(helpdesk@jobkorea.co.kr) subject:([잡코리아] 요청하신 2단계 인증번호)',
};

/**
 * 메인 실행 함수 — 잡코리아 인증번호 메일을 수집하여 시트에 저장
 */
function collectJobKoreaAuthCodes() {
  const sheet = SpreadsheetApp.openById(TWOFA_CONFIG.SPREADSHEET_ID).getSheetByName(TWOFA_CONFIG.SHEET_NAME);
  if (!sheet) {
    Logger.log(`[ERROR] "${TWOFA_CONFIG.SHEET_NAME}" 시트를 찾을 수 없습니다.`);
    return;
  }

  const existingMessageIds = getExistingMessageIds_(sheet);
  Logger.log(`[INFO] 기존 저장된 메시지 수: ${existingMessageIds.size}`);

  const threads = GmailApp.search(TWOFA_CONFIG.GMAIL_QUERY);
  Logger.log(`[INFO] 검색된 스레드 수: ${threads.length}`);

  const newRows = [];

  for (const thread of threads) {
    const messages = thread.getMessages();
    for (const message of messages) {
      const messageId = message.getId();

      if (existingMessageIds.has(messageId)) continue;

      const authCode = extractAuthCode_(message.getBody());
      if (!authCode) {
        Logger.log(`[WARN] 인증코드 추출 실패 — 메시지ID: ${messageId}`);
        continue;
      }

      const receivedDate = Utilities.formatDate(message.getDate(), "Asia/Seoul", "yyyy-MM-dd HH:mm:ss");

      newRows.push([receivedDate, messageId, authCode]);
      existingMessageIds.add(messageId);
      Logger.log(`[INFO] 신규 수집 — ${receivedDate} | ${messageId} | ${authCode}`);
    }
  }

  if (newRows.length === 0) {
    Logger.log("[INFO] 신규 메시지가 없습니다.");
    return;
  }

  const lastRow = sheet.getLastRow();
  sheet.getRange(lastRow + 1, 1, newRows.length, 3).setValues(newRows);
  sheet.getRange(2, 1, sheet.getLastRow() - 1, 3).sort({column: 1, ascending: true});  // ← 이 줄 추가
  Logger.log(`[INFO] ${newRows.length}건 저장 완료`);
}

/**
 * 시트에서 기존 메시지ID 목록을 Set으로 반환
 * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet
 * @returns {Set<string>}
 */
function getExistingMessageIds_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow <= 1) return new Set();

  const messageIdColumn = sheet.getRange(2, 2, lastRow - 1, 1).getValues();
  return new Set(messageIdColumn.flat().filter(String));
}

/**
 * 메일 본문(HTML)에서 6자리 인증코드 추출
 * HTML 태그 + HTML 엔티티(&nbsp; 등) 모두 제거 후 정규식 매칭
 * @param {string} htmlBody
 * @returns {string|null}
 */
function extractAuthCode_(htmlBody) {
  /* 1단계: HTML 태그 → 공백으로 치환 */
  let plainText = htmlBody.replace(/<[^>]+>/g, " ");

  /* 2단계: HTML 엔티티 디코딩 (&nbsp; &amp; &#160; 등) → 공백/문자로 치환 */
  plainText = plainText
    .replace(/&nbsp;/gi, " ")
    .replace(/&#160;/g, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&quot;/gi, '"');

  /* 3단계: 연속 공백/줄바꿈 정리 */
  plainText = plainText.replace(/\s+/g, " ");

  /* 4단계: "인증번호" 뒤에 오는 6자리 숫자 추출 (사이에 최대 30자 허용) */
  const match = plainText.match(/인증번호[\s\S]{0,30}?(\d{6})/);
  return match ? match[1] : null;
}

/**
 * 디버그 전용 — 첫 번째 메일의 본문을 로그에 출력하여 구조 확인
 * 문제 해결 후 삭제해도 됨
 */
function debugFirstEmailBody() {
  const threads = GmailApp.search(TWOFA_CONFIG.GMAIL_QUERY, 0, 1);
  if (threads.length === 0) {
    Logger.log("[DEBUG] 검색된 메일 없음");
    return;
  }

  const message = threads[0].getMessages()[0];
  const htmlBody = message.getBody();

  /* HTML 태그 제거 + 엔티티 디코딩 */
  let plainText = htmlBody.replace(/<[^>]+>/g, " ");
  plainText = plainText.replace(/&nbsp;/gi, " ").replace(/&#160;/g, " ");
  plainText = plainText.replace(/\s+/g, " ");

  /* "인증" 키워드 주변 100자만 출력 */
  const idx = plainText.indexOf("인증");
  if (idx >= 0) {
    const snippet = plainText.substring(Math.max(0, idx - 20), idx + 100);
    Logger.log(`[DEBUG] 인증 키워드 주변: "${snippet}"`);
  } else {
    Logger.log("[DEBUG] '인증' 키워드를 찾을 수 없음");
    Logger.log(`[DEBUG] 본문 앞 500자: "${plainText.substring(0, 500)}"`);
  }

  /* 추출 테스트 */
  const authCode = extractAuthCode_(htmlBody);
  Logger.log(`[DEBUG] 추출된 인증코드: ${authCode || "실패"}`);
}
