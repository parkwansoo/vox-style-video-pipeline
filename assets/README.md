# assets/ — 현재 활성 스타일 슬롯

이 폴더는 **지금 영상 제작에 쓰이는 스타일 한 벌**만 담는다.
스타일 원본과 레퍼런스는 전부 `styles/<스타일명>/`에 있다.

| 파일 | 뜻 |
|---|---|
| `style_reference.png` | 활성 스타일 시트. vox-video의 모든 이미지 생성이 이 파일을 참조한다 |
| `ACTIVE_STYLE` | 지금 활성인 스타일 폴더 이름 |

## 스타일 전환

```bash
cp styles/<새스타일>/style_reference.png assets/style_reference.png
echo "<새스타일>" > assets/ACTIVE_STYLE
```

스킬 코드는 `assets/style_reference.png` 경로만 알면 되므로 전환은 이 두 줄로 끝난다.
전환 후 만드는 영상 폴더에는 `style.txt`로 어떤 스타일을 썼는지 기록한다.
