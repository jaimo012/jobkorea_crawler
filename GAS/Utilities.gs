/**
 * ===================================================================
 * Utilities.gs - 공통 유틸리티 함수
 * ===================================================================
 */

/**
 * 이메일 회신기한을 계산한다.
 * 규칙: 다음날이 평일이면 다음날 오전 11시, 주말이면 월요일 오전 11시
 * * @returns {string} "3월 21일(금) 오전 11시" 형태의 문자열
 */
function calculateDeadline() {
  const now = new Date();
  const deadlineDate = new Date(now);
  deadlineDate.setDate(deadlineDate.getDate() + 1);

  const dayOfWeek = deadlineDate.getDay();
  if (dayOfWeek === 6) {
    // 토요일 → 월요일 (+2일)
    deadlineDate.setDate(deadlineDate.getDate() + 2);
  } else if (dayOfWeek === 0) {
    // 일요일 → 월요일 (+1일)
    deadlineDate.setDate(deadlineDate.getDate() + 1);
  }

  const DAY_NAMES = ['일', '월', '화', '수', '목', '금', '토'];
  const month = deadlineDate.getMonth() + 1;
  const day = deadlineDate.getDate();
  const dayName = DAY_NAMES[deadlineDate.getDay()];

  return `${month}월 ${day}일(${dayName}) 오전 11시`;
}

/**
 * "총 10년 8개월" 등의 문자열을 분석하여 연차와 경력시작일을 계산한다.
 * * @param {string} expString - 총경력 문자열 (예: "총 10년 8개월", "경력무" 등)
 * @returns {{ years: number, months: number, startDate: string }}
 */
function parseExperience(expString) {
  if (!expString) return { years: 0, months: 0, startDate: '' };
  
  const str = String(expString);
  const yearMatch = str.match(/(\d+)\s*년/);
  const monthMatch = str.match(/(\d+)\s*개월/);

  const years = yearMatch ? parseInt(yearMatch[1], 10) : 0;
  const months = monthMatch ? parseInt(monthMatch[1], 10) : 0;

  if (years === 0 && months === 0) return { years: 0, months: 0, startDate: '' };

  // 오늘 날짜에서 파싱된 년/개월 수를 빼서 시작일 역산
  const d = new Date();
  d.setFullYear(d.getFullYear() - years);
  d.setMonth(d.getMonth() - months);

  const startDate = Utilities.formatDate(d, "Asia/Seoul", "yyyy-MM-dd");
  return { years, months, startDate };
}
