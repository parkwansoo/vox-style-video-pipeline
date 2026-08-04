import { loadFont } from '@remotion/fonts';
import { staticFile } from 'remotion';
import {FONT_CATALOG} from './font-catalog.mjs';

// 드롭다운에 보이는 값(키=한글) → { family: CSS에서 쓸 이름, file: _fonts/ 아래 파일 }.
// 렌더/미리보기에서 "선택된 폰트 1개만" 그때 불러온다(lazy) → 다 불러와 느려지지 않음.
// 가변폰트(프리텐다드·SUIT)는 파일 하나로 굵기 전체 조절 가능. 나머지는 대표 굵기 1개.
export const FONTS: Record<string, {family: string; file: string}> = FONT_CATALOG;

export const FONT_KEYS = Object.keys(FONTS);

// 키로 폰트 로드(한 번만). 성공 시 CSS fontFamily로 쓸 이름을 반환.
const _cache = new Map<string, Promise<string>>();
export function loadFontByKey(key: string): Promise<string> {
  const f = FONTS[key];
  if (!f) return Promise.resolve('sans-serif');
  if (!_cache.has(key)) {
    _cache.set(
      key,
      loadFont({ family: f.family, url: staticFile('_fonts/' + f.file) }).then(() => f.family),
    );
  }
  return _cache.get(key)!;
}
