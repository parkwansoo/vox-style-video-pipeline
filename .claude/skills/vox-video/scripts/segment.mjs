// 원본 어절 + 어절별 시각으로 짧은 자막 조각을 만든다.
// 40~60대 가독성: 조각당 글자수 상한(maxChars)을 지키되, '끊는 위치 품질'을 점수화해
// 문장 전체를 최적 분할(DP)한다 — 구(句) 중간·의존명사 앞에서 갈리지 않게.
const SENT_END = /[.?!…]$/;

// 폭 단위는 '한글 한 글자 = 1'로 환산해 쓴다. 원본은 글자 수로 셌는데, 한글·영문·
// 숫자·공백의 실제 폭이 제각각이라 같은 글자 수도 화면 폭이 40%까지 차이 났다
// (28번 실측: 10자 "뒤집은 앰플이 있습니다."가 982px, 같은 10자가 720px).
// 한 줄에 반드시 담아야 하므로 글자 수가 아니라 폭으로 자른다.
let METRICS = null;
export function setCaptionMetrics(m) { METRICS = m; }

const clen = (s) => {
  const t = s.replace(/\s/g, '');
  if (!METRICS) return t.length;
  let w = 0;
  for (const ch of t) w += METRICS.chars[ch] ?? METRICS.hangul;
  return w / METRICS.hangul;
};
const spaceLen = () => (METRICS ? METRICS.space / METRICS.hangul : 0);
// 끝 문장부호/따옴표/괄호 제거(어미 판정용)
const stripEnd = (w) => w.replace(/[.?!…,、"'”’)\]】》]+$/u, '');

// 연결어미로 끝남(~서/~니까/~는데/~면/~고 등) → 좋은 끊김
// 20번 원본에 없던 '~라' 계열(아니라·이라·라고)과 '지만'을 추가했다. 없으면
// "성분이 / 아니라"처럼 대조 구문 한가운데가 갈린다(28번 실측). '라'는 단독으로
// 넣지 않는다 — 나라·소리처럼 명사 끝을 연결어미로 오인한다.
const CONNECTIVE = /(아니라|이라|라고|라는|지만|아서|어서|여서|니까|는데|은데|다가|거나|든지|도록|려면|려고|면서|고서|자마자|으므로|므로|고|며|서|면|자|든|되|여|니)$/u;
// 격조사 등 구 경계 조사 → 무난한 끊김
const PARTICLE_STRONG = /(에서|에게|한테|으로|까지|부터|보다|을|를|에|로|와|과|이나)$/u;
// 보조사·주격 등(절 중간에 잦음) → 약한 끊김
const PARTICLE_WEAK = /(은|는|이|가|도|만|의|나)$/u;
// 관형형·서술격 어미(대표 성분인 / 필요한 / 만들어진) → 뒤의 명사를 꾸미므로
// 여기서 끊어도 읽힌다. 원본에 없어 "구 중간"(25)으로 취급돼 어절 하나가 홀로
// 남는 분할이 자주 이겼다.
const ADNOMINAL = /(인|한|된|던)$/u;
// 다음 어절이 의존명사/보조사로 시작 → 그 앞에서 끊으면 안 됨
const BOUND_NEXT = /^(듯|것|거|수|줄|리|뿐|데|때|채|척|만큼|대로|바|지|등|및)([은는이가을를에도로와과의만나]|$)/u;

// 어절 j(문장 내 인덱스)에서 줄을 끊는 '나쁨' 점수(낮을수록 자연스러움). 문장 끝은 0.
function breakBadness(w, j, n) {
  if (j >= n - 1) return 0;
  const cur = w[j];
  const next = w[j + 1];
  const s = stripEnd(cur);
  let bad;
  if (/[,、]$/u.test(cur)) bad = 0;            // 쉼표 뒤: 최고의 끊김
  else if (CONNECTIVE.test(s)) bad = 3;         // 연결어미 뒤
  else if (PARTICLE_STRONG.test(s)) bad = 8;    // 격조사 뒤
  else if (ADNOMINAL.test(s)) bad = 10;         // 관형형 어미 뒤
  else if (PARTICLE_WEAK.test(s)) bad = 12;     // 보조사/주격 뒤
  else bad = 25;                                 // 구 중간(명사·관형어 등)
  if (BOUND_NEXT.test(next)) bad += 60;          // 다음이 의존명사 → 강하게 회피
  return bad;
}

// 문장(어절 인덱스 배열)을 maxChars 이하 줄들로, 총 끊김 나쁨 최소화(DP).
function wrapSentence(sent, words, maxChars) {
  const n = sent.length;
  if (n <= 1) return n ? [sent] : [];
  const w = sent.map((i) => words[i]);
  // 원본은 끝 문장부호를 읽기 폭에서 뺐지만, 폭 모드에서는 화면에 실제로 차지하는
  // 폭을 그대로 재야 한 줄이 보장된다(마침표 하나가 예산을 넘겨 두 줄이 됐다).
  const len = w.map((x) => clen(METRICS ? x : stripEnd(x)));
  const cost = new Array(n + 1).fill(Infinity);
  const prev = new Array(n + 1).fill(-1);
  cost[0] = 0;
  const sp = spaceLen();
  for (let end = 1; end <= n; end++) {
    let width = 0;
    for (let start = end - 1; start >= 0; start--) {
      width += len[start] + (start < end - 1 ? sp : 0);
      // 한 줄에 여러 어절인데 상한 초과면 더 늘리지 않음(단일 어절은 초과 허용)
      if (start < end - 1 && width > maxChars) break;
      if (cost[start] === Infinity) continue;
      const slack = Math.max(0, maxChars - width);
      // 한 어절만 남는 토막 억제. slack 패널티(0.05/글자)는 끊김 점수(8~25)에 비해
      // 너무 작아 "미백의" 같은 고아 조각이 이겼다. 예산의 45% 미만이면 가파르게
      // 벌점을 준다 — 문장 끝의 짧은 마무리는 대안이 더 나쁘면 그대로 살아남는다.
      const floor = maxChars * 0.45;
      const runt = width < floor ? (floor - width) * 3 : 0;
      const c = cost[start] + breakBadness(w, end - 1, n) + slack * 0.05 + runt;
      if (c < cost[end]) { cost[end] = c; prev[end] = start; }
    }
  }
  const bounds = [];
  let e = n;
  while (e > 0) { const s = prev[e]; bounds.unshift([s, e]); e = s; }
  return bounds.map(([s, en]) => sent.slice(s, en));
}

export function segmentCaptions(origWords, timings, opts = {}) {
  const maxChars = opts.maxChars ?? 16;
  const minDurMs = opts.minDurMs ?? 700;

  // 1) 어절을 문장으로 묶기
  const sentences = [];
  let cur = [];
  origWords.forEach((w, idx) => {
    cur.push(idx);
    if (SENT_END.test(w)) { sentences.push(cur); cur = []; }
  });
  if (cur.length) sentences.push(cur);

  // 2) 문장별 최적 줄바꿈
  const caps = [];
  for (const sent of sentences) {
    for (const ch of wrapSentence(sent, origWords, maxChars)) {
      const matchedCount = ch.filter((i) => timings[i].matched !== false).length;
      const conf = ch.length ? Math.round((matchedCount / ch.length) * 100) / 100 : 1;
      caps.push({
        text: ch.map((i) => origWords[i]).join(' '),
        startMs: Math.round(timings[ch[0]].start * 1000),
        endMs: Math.round(timings[ch[ch.length - 1]].end * 1000),
        conf,
        lowConf: conf < 0.6,
      });
    }
  }

  // 3) 최소 표시시간 보장(다음 조각 시작 침범 금지)
  for (let k = 0; k < caps.length; k++) {
    if (caps[k].endMs - caps[k].startMs < minDurMs) {
      const limit = k + 1 < caps.length ? caps[k + 1].startMs : Infinity;
      caps[k].endMs = Math.min(caps[k].startMs + minDurMs, limit);
    }
  }
  return caps;
}
