/**
 * ===================================================================
 * EmailService.gs - 제안수락 이메일 발송
 * ===================================================================
 */

/**
 * 제안수락자에게 요청사항 이메일을 발송한다.
 * 발송: alpha@kmong.com (GAS 실행 계정)
 * 참조: 담당 매니저 이메일
 * 수신: 제안수락자 이메일
 * * @param {Object} rowData - 시트 행 데이터 (컬럼명-값 매핑)
 * @param {Object} manager - 범례 매니저 정보 객체
 * @param {string} deadline - 회신기한 문자열 (예: "3월 21일(금) 오전 11시")
 */
function sendProposalEmail(rowData, manager, deadline) {
  const candidateName = rowData[COL.NAME];
  const candidateEmail = rowData[COL.EMAIL];
  const position = rowData[COL.POSITION] || ''; // 빈칸 방어코드 추가
  const taskDesc = rowData[COL.TASK_DESC] || '';
  const preferred = rowData[COL.PREFERRED] || '';
  const managerDisplayName = manager[LEGEND_COL.DISPLAY_NAME];
  const managerPhone = manager[LEGEND_COL.PHONE];
  const managerEmail = manager[LEGEND_COL.EMAIL];

  // position이 비어있을 경우 제목이 어색해지는 것을 방지 (선택적 처리)
  const positionTitle = position ? `${position} 포지션 관련` : '포지션';
  const subject = `[크몽] ${candidateName}님, ${positionTitle} 요청사항`;

  const emailParams = {
    candidateName, position, taskDesc, preferred,
    managerDisplayName, managerPhone, managerEmail, deadline
  };
  
  const htmlBody = buildEmailHtml(emailParams);
  const plainBody = buildEmailPlainText(emailParams);

  const ccFormatted = `"${managerDisplayName} (크몽 엔터프라이즈)" <${managerEmail}>`;
  const toFormatted = `"${candidateName}님" <${candidateEmail}>`;

  GmailApp.sendEmail(toFormatted, subject, plainBody, {
    cc: ccFormatted,
    htmlBody: htmlBody,
    name: EMAIL_SENDER_NAME
  });

  Logger.log(`이메일 발송 완료 → ${candidateEmail} (CC: ${managerEmail})`);
}

/**
 * 이메일 시그니처(-- 이하) HTML을 생성한다.
 * 포지션명, 수행업무, 우대사항을 포함한다.
 * * @param {string} position - 제안포지션
 * @param {string} taskDesc - 수행업무
 * @param {string} preferred - 우대사항
 * @returns {string} HTML 시그니처 문자열
 */
function buildSignatureHtml(position, taskDesc, preferred) {
  const P = 'style="margin: 0 0 16px 0;"';
  let signature = `<p ${P}><b>${position}</b></p>`;

  if (taskDesc) {
    signature += `<p ${P}>${taskDesc.replace(/\n/g, '<br>')}</p>`;
  }

  if (preferred) {
    signature += `<p ${P}>우대사항:<br>${preferred.replace(/\n/g, '<br>')}</p>`;
  }

  return signature;
}

/**
 * 이메일 시그니처(-- 이하) Plain Text를 생성한다.
 * * @param {string} position - 제안포지션
 * @param {string} taskDesc - 수행업무
 * @param {string} preferred - 우대사항
 * @returns {string} Plain Text 시그니처 문자열
 */
function buildSignaturePlainText(position, taskDesc, preferred) {
  let signature = `${position}`;

  if (taskDesc) {
    signature += `\n\n${taskDesc}`;
  }

  if (preferred) {
    signature += `\n\n우대사항:\n${preferred}`;
  }

  return signature;
}

/**
 * 이메일 HTML 본문을 생성한다.
 * * @param {Object} params - 이메일 파라미터 객체
 */
function buildEmailHtml(params) {
  const { candidateName, position, taskDesc, preferred, managerDisplayName, managerPhone, managerEmail, deadline } = params;

  // position 값이 있을 때만 구분선과 시그니처 HTML을 생성합니다.
  const signatureSectionHtml = position ? `
  <hr style="border: none; border-top: 1px solid #ccc; margin: 20px 0;">
  ${buildSignatureHtml(position, taskDesc, preferred)}` : '';

  const P = 'style="margin: 0 0 16px 0;"';
  const positionDisplay = position ? `<b>${position}</b> 포지션 ` : '';

  return `
<div style="font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; font-size: 14px; line-height: 1.8; color: #333;">
  <p ${P}>${candidateName}님 안녕하십니까.<br>크몽 엔터프라이즈 입니다.<br></p>

  <p ${P}>잡코리아에서 제안드린 ${positionDisplay}제안을 수락해주셔서 감사합니다.<br>
  고객사에 ${candidateName}님을 제안드리기 위해, 갖고 있는 프로필 한 부를 전달 부탁드리겠습니다.<br></p>

  <p ${P}><b>[요청사항]</b><br>
  - <b>개인이력카드 (혹은 이력서, 경력기술서 등)</b> 및 (해당시)포트폴리오<br>
  - <b>희망 월단가</b>: 월 &nbsp;_____ 만원 (세전, 3.3%)<br>
  - <b>투입 가능일</b>: __월 __일 이후 가능 (혹은 즉시 가능)<br>
  - <b>해당 포지션 관련 주요 경력 및 강점 (2~3줄)</b><br></p>

  <p ${P}><b>[회신기한]</b><br>
  - 상기 내용을 포함하여 <b>~${deadline}까지</b> 회신 요망<br>
  - 고객사에서 긴급히 요청하여 빠르게 회신 보내주실수록 투입 가능성이 높습니다.<br></p>

  <p ${P}><b>[회신처]</b><br>
  해당 이메일에 <b>"전체답장"</b>을 눌러 회신 요망<br>
  - 담당 매니저: ${managerDisplayName}<br>
  - 담당자 연락처: ${managerPhone}<br>
  - 담당자 이메일: ${managerEmail}<br></p>

  <p ${P}>갖고 계신 양식의 이력서가 있다면 해당 파일을 전달 부탁드립니다.<br>
  혹은 수정 가능한 버전(.docx, .hwp 등)의 이력서가 없다면 아래 양식을 다운 받아 작성 부탁드립니다.<br>
  <b>개인이력카드 양식</b>: <a href="${RESUME_TEMPLATE_URL}">다운로드</a><br></p>

  <p ${P}>감사합니다.<br></p>

  <p ${P} style="margin-bottom: 0;"><b>크몽 엔터프라이즈</b> 드림.</p>${signatureSectionHtml}
</div>`.trim();
}

/**
 * 이메일 Plain Text 본문을 생성한다 (HTML 미지원 클라이언트 폴백용).
 * * @param {Object} params - 이메일 파라미터 객체
 */
function buildEmailPlainText(params) {
  const { candidateName, position, taskDesc, preferred, managerDisplayName, managerPhone, managerEmail, deadline } = params;

  // position 값이 있을 때만 구분선(--)과 시그니처 텍스트를 생성합니다.
  const signatureSectionPlain = position ? `
--
${buildSignaturePlainText(position, taskDesc, preferred)}` : '';

  const positionDisplay = position ? `${position} 포지션 관련하여 ` : '';

  return `${candidateName}님 안녕하십니까.
크몽 엔터프라이즈 입니다.

잡코리아에서 제안드린 ${positionDisplay}제안을 수락해주셔서 감사합니다.
고객사에 ${candidateName}님을 제안드리기 위해, 가지고 계신 프로필 한 부를 전달 부탁드리겠습니다.

[요청사항]
- 개인이력카드 (혹은 이력서, 경력기술서 등) 및 (해당시)포트폴리오
- 희망 월단가: 월  _____ 만원 (세전, 3.3%)
- 투입 가능일: __월 __일 이후 가능 (혹은 즉시 가능)
- 해당 포지션 관련 주요 경력 및 강점 (2~3줄)

[회신기한]
- 상기 내용을 포함하여 ~${deadline}까지 회신 요망
- 고객사에서 긴급히 요청하여 빠르게 회신 보내주실수록 투입 가능성이 높습니다.

[회신처]
해당 이메일에 "전체답장"을 눌러 회신 요망
- 담당 매니저: ${managerDisplayName}
- 담당자 연락처: ${managerPhone}
- 담당자 이메일: ${managerEmail}

갖고 계신 양식의 이력서가 있다면 해당 파일을 전달 부탁드립니다.
혹은 수정 가능한 버전(.docx, .hwp 등)의 이력서가 없다면 아래 양식을 다운 받아 작성 부탁드립니다.
개인이력카드 양식: ${RESUME_TEMPLATE_URL}

감사합니다.

크몽 엔터프라이즈 드림.${signatureSectionPlain}`;
}
