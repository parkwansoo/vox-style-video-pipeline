// 렌더와 보드 미리보기가 같은 폰트 파일을 쓰도록 한곳에서 관리한다.
export const FONT_CATALOG = Object.freeze({
  'G마켓 산스': {family: 'GmarketSans', file: 'GmarketSansBold.otf'},
  '프리텐다드': {family: 'Pretendard', file: 'PretendardVariable.ttf'},
  'SUIT': {family: 'SUITKR', file: 'SUIT-Variable.ttf'},
  '배민 을지로': {family: 'BMEuljiro', file: 'BMEuljiro.otf'},
  '배민 꾸불림': {family: 'BMKkubulim', file: 'BMKkubulim.otf'},
  '배민 주아': {family: 'BMJua', file: 'BMJua.otf'},
  '배민 도현': {family: 'BMDoHyeon', file: 'BMDoHyeon.otf'},
  '배민 연성': {family: 'BMYeongSung', file: 'BMYeongSung.otf'},
  '배민 기랑해랑': {family: 'BMKirangHaerang', file: 'BMKirangHaerang.otf'},
  '배민 한나체 Air': {family: 'BMHannaAir', file: 'BMHannaAir.otf'},
  '배민 한나체 Pro': {family: 'BMHannaPro', file: 'BMHannaPro.otf'},
  '배민 한나는 열한살': {family: 'BMHanna11yrs', file: 'BMHanna11yrs.otf'},
  '잘난체2': {family: 'Jalnan2', file: 'Jalnan2.otf'},
  '경기천년바탕': {family: 'GyeonggiBatang', file: 'GyeonggiBatang-Bold.otf'},
  '경기천년제목': {family: 'GyeonggiTitle', file: 'GyeonggiTitle-Bold.otf'},
  '구름 산스': {family: 'GoormSans', file: 'GoormSans-Bold.otf'},
  '나눔손글씨 꽃내음': {family: 'NanumFlower', file: 'NanumFlower.ttf'},
  '나눔손글씨 나의 아내': {family: 'NanumWife', file: 'NanumWife.ttf'},
  '눈누 기초고딕': {family: 'NoonnuBasicGothic', file: 'NoonnuBasicGothic.otf'},
  '둥근모꼴': {family: 'DungGeunMo', file: 'DungGeunMo.otf'},
  '마루 부리': {family: 'MaruBuri', file: 'MaruBuri-Bold.ttf'},
  '삼육대체': {family: 'Samyook', file: 'Samyook-Regular.otf'},
  '엘리스 DX널리': {family: 'EliceDXNeolli', file: 'EliceDXNeolli-Bold.otf'},
  '페이퍼로지': {family: 'Paperlogy', file: 'Paperlogy-Bold.otf'},
  '평창 평화체': {family: 'PyeongChangPeace', file: 'PyeongChangPeace-Bold.otf'},
  'Helvetica': {family: 'HelveticaLocal', file: 'Helvetica-Bold.ttf'},
  'MBC 1961굴림': {family: 'MBC1961Gulim', file: 'MBC1961Gulim.otf'},
  'Noto Sans KR': {family: 'NotoSansKRLocal', file: 'NotoSansKR-Bold.otf'},
  'SB 어그로': {family: 'SBAggro', file: 'SBAggro-Bold.otf'},
});

export function fontDescriptor(key) {
  return FONT_CATALOG[key] ?? null;
}
