/**
 * ===================================================================
 * SmsService.gs - NHN Cloud SMS v3.0 문자 발송
 * ===================================================================
 * 담당자별 APP_KEY/SECRET_KEY를 스크립트 속성에서 읽어 SMS를 발송한다.
 * 발신번호는 범례 시트의 매니저 연락처를 사용한다 (NHN Cloud에 등록 필수).
 * ===================================================================
 */

/**
 * 제안수락자에게 안내 문자를 발송한다.
 * 
 * @param {Object} rowData - 시트 행 데이터
 * @param {Object} manager - 범례 매니저 정보 객체
 */
function sendSms(rowData, manager) {
  const candidateName = rowData[COL.NAME];
  const recipientPhone = stripHyphens(rowData[COL.PHONE]);
  const senderPhone = stripHyphens(manager[LEGEND_COL.PHONE]);

  const messageBody = `안녕하세요, ${candidateName}님 잡코리아로 제안 드린 크몽입니다\n메일 확인 부탁드립니다`;

  const { appKey, secretKey } = getManagerSmsKeys(manager);

  const url = `${SMS_API_BASE_URL}/${appKey}/sender/sms`;

  const payload = {
    body: messageBody,
    sendNo: senderPhone,
    recipientList: [
      {
        recipientNo: recipientPhone
      }
    ]
  };

  const options = {
    method: 'post',
    contentType: 'application/json;charset=UTF-8',
    headers: {
      'X-Secret-Key': secretKey
    },
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch(url, options);
  const responseCode = response.getResponseCode();
  const responseBody = JSON.parse(response.getContentText());

  Logger.log(`SMS API 응답 [${responseCode}]: ${JSON.stringify(responseBody)}`);

  if (responseCode !== 200 || !responseBody.header || !responseBody.header.isSuccessful) {
    const errorMsg = responseBody.header
      ? responseBody.header.resultMessage
      : `HTTP ${responseCode}`;
    throw new Error(`SMS 발송 실패: ${errorMsg}`);
  }

  Logger.log(`SMS 발송 완료 → ${recipientPhone}`);
}

/**
 * 매니저의 NHN Cloud SMS API 키를 스크립트 속성에서 조회한다.
 * 
 * @param {Object} manager - 범례 매니저 정보 객체
 * @returns {{ appKey: string, secretKey: string }}
 */
function getManagerSmsKeys(manager) {
  const nickname = manager[LEGEND_COL.NICKNAME];
  const prefix = MANAGER_NICKNAME_TO_PREFIX[nickname];

  if (!prefix) {
    throw new Error(`매니저 닉네임 "${nickname}"에 대한 API 키 매핑을 찾을 수 없습니다.`);
  }

  const props = PropertiesService.getScriptProperties();
  const appKey = props.getProperty(`${prefix}_APP_KEY`);
  const secretKey = props.getProperty(`${prefix}_SECRET_KEY`);

  if (!appKey || !secretKey) {
    throw new Error(`스크립트 속성에 ${prefix}_APP_KEY 또는 ${prefix}_SECRET_KEY가 없습니다.`);
  }

  return { appKey, secretKey };
}

/**
 * 전화번호에서 하이픈을 제거한다.
 * "010-1234-5678" → "01012345678"
 * 
 * @param {string} phone - 하이픈 포함 전화번호
 * @returns {string} 하이픈 제거된 전화번호
 */
function stripHyphens(phone) {
  return String(phone).replace(/-/g, '');
}
