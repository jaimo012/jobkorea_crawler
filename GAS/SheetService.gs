/**
 * ===================================================================
 * SheetService.gs - 시트 읽기/쓰기 유틸리티
 * ===================================================================
 */

/**
 * 범례 시트에서 매니저 정보를 로드하여 Map으로 반환한다.
 * Key: 매니저_이름 (예: "유강희"), Value: 매니저 정보 객체
 * * @param {Spreadsheet} spreadsheet - 스프레드시트 객체
 * @returns {Object} 매니저명 → 매니저정보 매핑 객체
 */
function loadManagerMap(spreadsheet) {
  const legendSheet = spreadsheet.getSheetByName(LEGEND_SHEET_NAME);
  const legendData = legendSheet.getDataRange().getValues();
  const headers = legendData[0];
  const managerMap = {};

  legendData.slice(1).forEach(row => {
    const manager = {};
    headers.forEach((header, colIndex) => {
      manager[header] = row[colIndex];
    });

    const managerName = manager[LEGEND_COL.NAME];
    if (managerName) {
      managerMap[managerName] = manager;
    }
  });

  return managerMap;
}

/**
 * 대상 시트에서 미처리 행을 찾는다.
 * 조건: 휴대전화번호가 존재하고, (문자안내가 비어있거나 OR 시트입력이 비어있는 경우)
 * * @param {Sheet} sheet - 대상 시트
 * @returns {{ headers: string[], rows: any[][], rowNumbers: number[] }}
 */
function getUnprocessedRows(sheet) {
  const allData = sheet.getDataRange().getValues();
  const headers = allData[0].map(String);

  const phoneColIndex = headers.indexOf(COL.PHONE);
  const smsStatusColIndex = headers.indexOf(COL.SMS_STATUS);
  const sheetStatusColIndex = headers.indexOf(COL.SHEET_STATUS);

  if (phoneColIndex === -1 || smsStatusColIndex === -1 || sheetStatusColIndex === -1) {
    throw new Error(`필수 컬럼을 찾을 수 없습니다. (헤더명 불일치 확인)`);
  }

  const rows = [];
  const rowNumbers = [];

  allData.slice(1).forEach((row, index) => {
    const phone = String(row[phoneColIndex]).trim();
    const smsStatus = String(row[smsStatusColIndex]).trim();
    const sheetStatus = String(row[sheetStatusColIndex]).trim();

    const hasPhone = phone !== '' && phone !== 'undefined';
    
    // 이메일/문자 발송이 아직 안 되었거나, 타겟 DB 시트 입력이 아직 안 된 건을 모두 대상에 포함
    const notProcessedSms = (smsStatus === '' || smsStatus === 'undefined');
    const notProcessedDb = (sheetStatus === '' || sheetStatus === 'undefined');

    if (hasPhone && (notProcessedSms || notProcessedDb)) {
      rows.push(row);
      rowNumbers.push(index + 2); // 1-indexed, 헤더 제외
    }
  });

  return { headers, rows, rowNumbers };
}

/**
 * 헤더 배열과 행 데이터를 Object로 매핑한다.
 * * @param {string[]} headers - 헤더 배열
 * @param {any[]} row - 행 데이터 배열
 * @returns {Object} 컬럼명 → 값 매핑 객체
 */
function mapRowToObject(headers, row) {
  const obj = {};
  headers.forEach((header, index) => {
    obj[header] = row[index] !== undefined ? String(row[index]).trim() : '';
  });
  return obj;
}

/**
 * 시트의 특정 행에 상태값을 일괄 업데이트한다.
 * * @param {Sheet} sheet - 대상 시트
 * @param {string[]} headers - 헤더 배열
 * @param {number} rowNumber - 행 번호 (1-indexed)
 * @param {Object} statusMap - { 컬럼명: 상태값 } 객체
 */
function updateRowStatus(sheet, headers, rowNumber, statusMap) {
  Object.entries(statusMap).forEach(([columnName, value]) => {
    const colIndex = headers.indexOf(columnName);
    if (colIndex === -1) {
      Logger.log(`경고: "${columnName}" 컬럼을 찾을 수 없습니다.`);
      return;
    }
    sheet.getRange(rowNumber, colIndex + 1).setValue(value);
  });
}
