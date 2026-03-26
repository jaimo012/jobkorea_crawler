/**
 * ===================================================================
 * Main.gs - 잡코리아 제안수락 자동화 메인 함수
 * ===================================================================
 * 실행 순서: 이메일 발송 → 문자 발송 → 슬랙 안내 → DB 시트 동기화 → 시트 업데이트
 * ===================================================================
 */

function processNewAcceptances() {
  Logger.log('===== 제안수락 자동화 시작 =====');
  Logger.log(`대상 시트: ${TARGET_SHEET_NAME}`);

  try {
    const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
    
    // Step 1: 범례 시트에서 매니저 정보 로드
    const managerMap = loadManagerMap(spreadsheet);
    Logger.log(`Step 1 완료: 매니저 ${Object.keys(managerMap).length}명 로드`);

    // Step 2: 대상 시트에서 미처리 행 찾기
    const targetSheet = spreadsheet.getSheetByName(TARGET_SHEET_NAME);
    if (!targetSheet) {
      throw new Error(`"${TARGET_SHEET_NAME}" 시트를 찾을 수 없습니다.`);
    }

    const { headers, rows, rowNumbers } = getUnprocessedRows(targetSheet);
    Logger.log(`Step 2 완료: 미처리 ${rows.length}건 발견`);

    if (rows.length === 0) {
      Logger.log('처리할 건이 없습니다. 종료.');
      return;
    }

    // Step 3: 각 행 순차 처리
    let successCount = 0;
    let failCount = 0;

    rows.forEach((row, index) => {
      const rowNumber = rowNumbers[index];
      const rowData = mapRowToObject(headers, row);
      const candidateName = rowData[COL.NAME];
      const managerName = rowData[COL.MANAGER];

      Logger.log(`\n--- [${rowNumber}행] ${candidateName} 처리 시작 ---`);

      const manager = managerMap[managerName];
      if (!manager) {
        Logger.log(`[${rowNumber}행] ❌ 담당자 "${managerName}" 범례 매칭 실패 → 건너뜀`);
        failCount++;
        return;
      }

      const deadline = calculateDeadline();

      // [방어코드] 이미 발송된 건은 재발송하지 않고 상태 유지
      let emailStatus = rowData[COL.EMAIL_STATUS] || '';
      if (emailStatus !== SENT_MARKER && emailStatus !== PRIVATE_MARKER) {
        emailStatus = processEmail(rowData, manager, deadline, rowNumber);
      }

      let smsStatus = rowData[COL.SMS_STATUS] || '';
      if (smsStatus !== SENT_MARKER && smsStatus !== PRIVATE_MARKER) {
        smsStatus = processSms(rowData, manager, rowNumber);
      }

      let slackStatus = rowData[COL.SLACK_STATUS] || '';
      if (slackStatus !== SENT_MARKER && slackStatus !== PRIVATE_MARKER) {
        slackStatus = processSlack(rowData, manager, smsStatus, emailStatus, rowNumber);
      }

      // ④ 회원기준정보 DB 시트 동기화
      // ★ 변경점: '미입력(SYNC_SKIPPED_MARKER)' 상태일 때도 스킵하도록 방어코드 추가
      let sheetStatus = rowData[COL.SHEET_STATUS] || '';
      if (sheetStatus !== SYNC_COMPLETE_MARKER && sheetStatus !== SYNC_SKIPPED_MARKER && sheetStatus !== PRIVATE_MARKER) {
        sheetStatus = processDbSync(rowData, manager, rowNumber);
      }

      // ⑤ 상태 업데이트 결과 시트에 쓰기
      updateRowStatus(targetSheet, headers, rowNumber, {
        [COL.SMS_STATUS]: smsStatus,
        [COL.EMAIL_STATUS]: emailStatus,
        [COL.SLACK_STATUS]: slackStatus,
        [COL.SHEET_STATUS]: sheetStatus
      });

      Logger.log(`[${rowNumber}행] ✅ ${candidateName} 처리 완료`);
      successCount++;

      // API Rate Limit 방지 (1초 대기)
      Utilities.sleep(1000);
    });

    Logger.log(`\n===== 처리 완료: 성공 ${successCount}건 / 실패 ${failCount}건 =====`);

  } catch (error) {
    Logger.log(`❌ 치명적 오류: ${error.message}`);
    Logger.log(`Stack: ${error.stack}`);
  }
}

/** 이메일 처리 래퍼 함수 */
function processEmail(rowData, manager, deadline, rowNumber) {
  const email = rowData[COL.EMAIL];
  if (String(manager[LEGEND_COL.EMAIL_ENABLED]).toUpperCase() === 'FALSE') return '발송제외';
  if (email === PRIVATE_MARKER) return PRIVATE_MARKER;
  if (!email || email === '' || email === 'undefined') return '이메일없음';

  try {
    sendProposalEmail(rowData, manager, deadline);
    return SENT_MARKER;
  } catch (error) {
    return `오류: ${error.message}`;
  }
}

/** SMS 처리 래퍼 함수 */
function processSms(rowData, manager, rowNumber) {
  const phone = rowData[COL.PHONE];
  if (String(manager[LEGEND_COL.SMS_ENABLED]).toUpperCase() === 'FALSE') return '발송제외';
  if (phone === PRIVATE_MARKER) return PRIVATE_MARKER;

  try {
    sendSms(rowData, manager);
    return SENT_MARKER;
  } catch (error) {
    return `오류: ${error.message}`;
  }
}

/** Slack 처리 래퍼 함수 */
function processSlack(rowData, manager, smsStatus, emailStatus, rowNumber) {
  if (String(manager[LEGEND_COL.SLACK_ENABLED]).toUpperCase() === 'FALSE') return '발송제외';
  try {
    sendSlackNotification(rowData, manager, smsStatus, emailStatus);
    return SENT_MARKER;
  } catch (error) {
    return `오류: ${error.message}`;
  }
}
