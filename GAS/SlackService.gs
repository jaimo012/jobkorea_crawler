/**
 * ===================================================================
 * SlackService.gs - Slack Incoming Webhook 알림 발송
 * ===================================================================
 */

/**
 * 제안수락 안내를 Slack 채널에 발송한다.
 * 
 * @param {Object} rowData - 시트 행 데이터
 * @param {Object} manager - 범례 매니저 정보 객체
 * @param {string} smsStatus - 문자 발송 결과 ("발송완료" / "비공개" / "오류:...")
 * @param {string} emailStatus - 이메일 발송 결과 ("발송완료" / "비공개" / "오류:...")
 */
function sendSlackNotification(rowData, manager, smsStatus, emailStatus) {
  const slackUserId = manager[LEGEND_COL.SLACK_ID];
  const candidateName = rowData[COL.NAME];
  const position = rowData[COL.POSITION];
  const phone = rowData[COL.PHONE];
  const email = rowData[COL.EMAIL];

  const now = Utilities.formatDate(new Date(), 'Asia/Seoul', 'yyyy.MM.dd HH:mm');

  const phoneDisplay = buildPhoneDisplay(phone, smsStatus);
  const emailDisplay = buildEmailDisplay(email, emailStatus);
  const resumeDisplay = buildResumeDisplay(rowData);
  const sheetUrl = SHEET_URLS[TARGET_SHEET_NAME] || SHEET_URLS['RAW'];

  const message = [
    `<@${slackUserId}> 🎉 *${position} 수락 안내*`,
    now,
    '',
    `*${position}*`,
    `🧑‍💻 *이름* ${candidateName}`,
    `📞 *연락처* ${phoneDisplay}`,
    `📤 *이메일* ${emailDisplay}`,
    '',
    resumeDisplay,
    `📂 *시트* <${sheetUrl}|바로가기>`
  ].join('\n');

  const payload = { text: message };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(SLACK_WEBHOOK_URL, options);
  const responseCode = response.getResponseCode();

  if (responseCode !== 200) {
    throw new Error(`Slack 발송 실패: HTTP ${responseCode} - ${response.getContentText()}`);
  }

  Logger.log(`Slack 알림 발송 완료 → <@${slackUserId}>`);
}

/**
 * 연락처 표시 문자열을 생성한다.
 * 예: "010-1234-5678 (문자 발송완료)" 또는 "비공개"
 */
function buildPhoneDisplay(phone, smsStatus) {
  if (phone === PRIVATE_MARKER) {
    return '비공개';
  }
  return `${phone} (문자 ${smsStatus})`;
}

/**
 * 이메일 표시 문자열을 생성한다.
 * 예: "test@naver.com (메일 발송완료)" 또는 "비공개"
 */
function buildEmailDisplay(email, emailStatus) {
  if (email === PRIVATE_MARKER) {
    return '비공개';
  }
  return `${email} (메일 ${emailStatus})`;
}

/**
 * 이력서/첨부파일 표시 문자열을 생성한다.
 * 📃*이력서* <URL|다운로드> / <URL|첨부파일1> / ...
 */
function buildResumeDisplay(rowData) {
  const parts = [];

  const resumeFileUrl = String(rowData[COL.RESUME_FILE_URL] || '').trim();
  const resumeUrl = String(rowData[COL.RESUME_URL] || '').trim();
  const downloadUrl = (resumeFileUrl.startsWith('http') ? resumeFileUrl : '') ||
                      (resumeUrl.startsWith('http') ? resumeUrl : '');

  if (downloadUrl) {
    parts.push(`<${downloadUrl}|다운로드>`);
  }

  const attachmentColumns = [
    { key: COL.ATTACHMENT_1, label: '첨부파일1' },
    { key: COL.ATTACHMENT_2, label: '첨부파일2' },
    { key: COL.ATTACHMENT_3, label: '첨부파일3' }
  ];

  attachmentColumns.forEach(({ key, label }) => {
    const url = String(rowData[key] || '').trim();
    if (url && url !== 'undefined' && url !== 'null' && url.startsWith('http')) {
      parts.push(`<${url}|${label}>`);
    }
  });

  if (parts.length === 0) {
    return '📃 *이력서* 없음';
  }

  return `📃 *이력서* ${parts.join(' / ')}`;
}
