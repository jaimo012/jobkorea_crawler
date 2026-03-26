/**
 * ===================================================================
 * MemberSyncService.gs - 회원기준정보 DB 시트 동기화 로직
 * ===================================================================
 */

/** 신규 데이터 삽입 시 최소 시작 행 번호 (요구사항: 6849 로우 이후) */
const MIN_INSERT_ROW = 6849;

/**
 * DB 동기화를 처리하고 결과 상태를 반환한다.
 */
function processDbSync(rowData, manager, rowNumber) {
  const phone = rowData[COL.PHONE];
  
  if (phone === PRIVATE_MARKER) {
    Logger.log(`[${rowNumber}행] 🗄️ 전화번호 비공개 → DB 동기화 제외 ("미입력" 처리)`);
    return SYNC_SKIPPED_MARKER; // "미입력"
  }

  try {
    syncToMemberDb(rowData, manager);
    Logger.log(`[${rowNumber}행] 🗄️ DB 동기화 완료`);
    return SYNC_COMPLETE_MARKER; // "입력완료"
  } catch (error) {
    Logger.log(`[${rowNumber}행] 🗄️ DB 동기화 오류: ${error.message}`);
    return `오류: ${error.message}`;
  }
}

/**
 * 회원기준정보 시트에 후보자를 찾아서 업데이트(다중 매칭 지원)하거나 신규로 삽입한다.
 * @param {Object} rowData - RAW 시트의 행 데이터
 * @param {Object} manager - 범례 시트의 매니저 정보
 */
function syncToMemberDb(rowData, manager) {
  const targetSpreadsheet = SpreadsheetApp.openById(MEMBER_DB_SPREADSHEET_ID);
  const targetSheet = targetSpreadsheet.getSheetByName(MEMBER_DB_SHEET_NAME);

  if (!targetSheet) {
    throw new Error(`대상 시트 "${MEMBER_DB_SHEET_NAME}"를 찾을 수 없습니다.`);
  }

  const allData = targetSheet.getDataRange().getValues();
  
  // 데이터 정제: 전화번호에서 숫자만 추출 ("-" 제거)
  const rawPhone = String(rowData[COL.PHONE] || '');
  const phoneDigits = rawPhone.replace(/\D/g, ''); 
  
  const position = rowData[COL.POSITION] || '포지션미상';
  const nickname = manager[LEGEND_COL.NICKNAME] || '미상';
  
  const todayDate = new Date();
  const todayYymmdd = Utilities.formatDate(todayDate, "Asia/Seoul", "yyMMdd");
  const todayYyyyMmDd = Utilities.formatDate(todayDate, "Asia/Seoul", "yyyy-MM-dd");
  
  // 기본 컨텍 히스토리 로그 (기존 회원 업데이트용)
  const baseHistoryLog = `${todayYymmdd}) ${position} 제안 수락_${nickname}`;

  let matchedRowIndices = [];

  // 1. 기존 핸드폰 번호 검색 (H열, 배열 인덱스 7)
  for (let i = 1; i < allData.length; i++) {
    const existingPhone = String(allData[i][7]).replace(/\D/g, '');
    if (existingPhone !== '' && existingPhone === phoneDigits) {
      matchedRowIndices.push(i);
    }
  }

  // 2. 분기 처리 (업데이트 vs 신규 삽입)
  if (matchedRowIndices.length > 0) {
    /* ----- [기존 회원 업데이트 - 중복된 모든 행 적용] ----- */
    matchedRowIndices.forEach(index => {
      const rowNum = index + 1; // getRange는 1-indexed
      const currentHistory = String(allData[index][13] || '').trim(); // N열 (인덱스 13)
      
      // 기존 회원은 기본 포맷만 사용
      const newHistory = currentHistory ? `${baseHistoryLog}\n${currentHistory}` : baseHistoryLog;
      targetSheet.getRange(rowNum, 14).setValue(newHistory);
    });

  } else {
    /* ----- [신규 회원 삽입 (6849 로우 이후)] ----- */
    let emptyRowIndex = -1;
    
    // 배열 인덱스는 0부터 시작하므로 6849행은 인덱스 6848입니다.
    const startIndex = MIN_INSERT_ROW - 1; 
    
    // 6849행 이후의 데이터가 존재할 때만 빈칸 탐색
    if (allData.length > startIndex) {
      for (let i = startIndex; i < allData.length; i++) {
        if (!allData[i][2] || String(allData[i][2]).trim() === '') { // C열(인덱스 2) 기준 빈칸
          emptyRowIndex = i;
          break;
        }
      }
    }

    let insertRow;
    if (emptyRowIndex !== -1) {
      // 6849행 이후에서 빈칸을 찾은 경우
      insertRow = emptyRowIndex + 1;
    } else {
      // 빈칸이 없거나 전체 데이터가 6849행보다 적은 경우
      insertRow = Math.max(targetSheet.getLastRow() + 1, MIN_INSERT_ROW);
    }

    // 신규 회원을 위한 프로필 정보 추출 및 상세 히스토리 로그 생성
    const name = rowData[COL.NAME] || '';
    const email = rowData[COL.EMAIL] || '';
    const gender = rowData[COL.GENDER] || '-';
    const age = rowData[COL.AGE] || '-';
    const education = rowData[COL.EDUCATION] || '-';
    const experienceText = rowData[COL.EXPERIENCE] || '-';
    
    const expData = parseExperience(rowData[COL.EXPERIENCE]); // Utilities 함수로 연차/날짜 역산

    // ★ 신규 등록자 전용 상세 히스토리 문자열 조합
    const detailedHistoryLog = `${baseHistoryLog}\n- ${gender} / ${age} / ${education} / ${experienceText}`;

    // 업데이트할 열 배열 (B열 ~ N열, 총 13개 컬럼의 값을 한 번에 덮어씀)
    const newValues = [
      todayYyyyMmDd,      // B: 등록일자
      nickname,           // C: 등록인
      "잡코리아",         // D: 출처
      "",                 // E: 직무
      name,               // F: 성명
      email,              // G: 이메일
      phoneDigits,        // H: 핸드폰
      expData.startDate,  // I: 경력시작일
      expData.years || "",// J: 년차
      "",                 // K: 기술1
      "",                 // L: 희망급여
      "",                 // M: 종료일자
      detailedHistoryLog  // N: 히스토리 (상세 버전 적용)
    ];

    // B열(2번째 열)부터 가로로 13칸 범위를 잡아 배열 삽입
    targetSheet.getRange(insertRow, 2, 1, 13).setValues([newValues]);
  }
}

/**
 * ===================================================================
 * [테스트 전용 함수] DB 동기화 단독 테스트 (14번째 행 기준)
 * ===================================================================
 */
function testDbSyncOnly() {
  Logger.log('=== DB 동기화 단독 테스트 시작 ===');
  
  try {
    const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
    const managerMap = loadManagerMap(spreadsheet);
    const targetSheet = spreadsheet.getSheetByName(TARGET_SHEET_NAME);
    const allData = targetSheet.getDataRange().getValues();
    
    if (allData.length < 14) {
      Logger.log('테스트할 데이터가 부족합니다. 시트에 14행 이상 데이터가 있는지 확인해주세요.');
      return;
    }
    
    const headers = allData[0].map(String);
    const testRowIndex = 13; // 14행 테스트 유지
    
    const row = allData[testRowIndex];
    const rowData = mapRowToObject(headers, row);
    
    const candidateName = rowData[COL.NAME];
    const managerName = rowData[COL.MANAGER];
    const manager = managerMap[managerName];
    
    if (!manager) {
      Logger.log(`❌ 담당자 "${managerName}" 범례 매칭 실패`);
      return;
    }
    
    Logger.log(`테스트 대상자 (시트 14행): ${candidateName} (담당자: ${manager[LEGEND_COL.NICKNAME]})`);
    Logger.log(`전화번호: ${rowData[COL.PHONE]}`);
    
    // 테스트에서는 상태 마커만 반환받고 시트에 기록하지 않습니다.
    const resultStatus = processDbSync(rowData, manager, 14);
    
    Logger.log(`✅ DB 동기화 단독 테스트 완료! (예상 시트 기록 상태: [${resultStatus}])`);
    
  } catch (error) {
    Logger.log(`❌ 테스트 중 오류 발생: ${error.message}`);
    Logger.log(error.stack);
  }
}
