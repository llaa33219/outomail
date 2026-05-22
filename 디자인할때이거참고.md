# BLP Main Design Language

> **Philosophy**: 난해함, 유동성, 몽환적  
> 각진 모서리와 미세한 투명도, 그리고 하프톤의 몽환적 리듬이 공존하는 디자인 언어.

---

## 0. Cardinal Rules (절대 금기)

1. **모든 모서리는 완전히 각짐** — `border-radius: 0`
2. **Hover/Focus 시 크기 변경 금지** — `transform: scale()` 절대 사용 불가
3. **어떠한 경우에도 테두리는 존재하지 않음** — `border: none` / `border: 0` (예외 없음)

> 테두리 없이 요소를 구분하려면: 배경색 대비, 투명도 차이, offset 그림자, 여백을 사용한다.

---

## 1. Color Palette (Expanded)

### Primary Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Blue | `#007BFF` | 주요 액션, 브랜드 컬러 |
| BLP Red | `#FF0505` | 경고, 강조 |
| BLP Yellow | `#FFEA00` | 주의, 하이라이트 |
| BLP Green | `#00D620` | 성공, 긍정 |
| BLP Purple | `#AE00FF` | 특별, 창작 |
| BLP Dark | `#00193D` | 텍스트, 헤드라인 |
| BLP White | `#FAFCFF` | 순수 배경, 텍스트(어두운 배경용) |

### Deep Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Deep Blue | `#005BDD` | 호버/액티브 상태, 그림자 |
| BLP Deep Red | `#DB0000` | 강조 상태 |
| BLP Deep Yellow | `#EBD700` | 주의 상태 |
| BLP Deep Green | `#00B21B` | 성공 상태 |
| BLP Deep Purple | `#9200D6` | 특별 상태 |

### Ultra Deep Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Ultra Deep Blue | `#0026A3` | 그림자, 딥 포커스 |
| BLP Ultra Deep Red | `#A30000` | 강한 경고 |
| BLP Ultra Deep Yellow | `#B2A400` | 강한 주의 |
| BLP Ultra Deep Green | `#00B21B` | 강한 성공 |
| BLP Ultra Deep Purple | `#650094` | 강한 창작 |

### Light Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Light Blue | `#DBEDFF` | 배경, 비활성 상태 |
| BLP Light Red | `#FF0505` | (투명도 20% 권장) 미세 강조 |
| BLP Light Yellow | `#FFEA00` | (투명도 20% 권장) 미세 하이라이트 |
| BLP Light Green | `#00D620` | (투명도 20% 권장) 미세 성공 |
| BLP Light Purple | `#AE00FF` | (투명도 20% 권장) 미세 특별 |
| BLP Light Dark Blue | `#005BDD` | (투명도 20% 권장) 미세 액션 |
| BLP Light Dark | `#B9C7DA` | 서브 텍스트, 구분선 |

### Light Deep Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Light Deep Blue | `#BDCBDB` | 서브 배경, 카드 배경 |
| BLP Light Deep Red | `#DBBDBD` | 서브 배경, 경고 톤 |
| BLP Light Deep Yellow | `#DBD9BD` | 서브 배경, 주의 톤 |
| BLP Light Deep Green | `#BDDBC1` | 서브 배경, 성공 톤 |
| BLP Light Deep Purple | `#D2BDDB` | 서브 배경, 창작 톤 |
| BLP Light Deep Dark Blue | `#BDC3DB` | 서브 배경, 액션 톤 |
| BLP Light Deep Dark | `#C7CBD1` | 서브 텍스트, 구분선 |

### Light Ultra Deep Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Light Ultra Deep Blue | `#8598AD` | 딥 서브 배경 |
| BLP Light Ultra Deep Red | `#AD8585` | 딥 서브 배경 |
| BLP Light Ultra Deep Yellow | `#ADAA85` | 딥 서브 배경 |
| BLP Light Ultra Deep Green | `#85AD8B` | 딥 서브 배경 |
| BLP Light Ultra Deep Purple | `#A085AD` | 딥 서브 배경 |
| BLP Light Ultra Deep Dark Blue | `#858DAD` | 딥 서브 배경 |
| BLP Light Ultra Deep Dark | `#94989E` | 딥 서브 텍스트 |

### Paper Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP Paper Orange | `#F9F1E5` | 페이퍼 배경, 웜톤 |
| BLP Paper Green | `#EAF7EF` | 페이퍼 배경, 내추럴 |
| BLP Paper Purple | `#F1F0F5` | 페이퍼 배경, 창작 |
| BLP Paper Brown | `#F5F2E9` | 페이퍼 배경, 어스톤 |
| BLP Paper Pink | `#F1E8EC` | 페이퍼 배경, 소프트 |
| BLP Paper Blue | `#F4F8FC` | 페이퍼 배경, 쿨톤 |
| BLP Paper Lime | `#F2F6ED` | 페이퍼 배경, 라이트 |

### Background Colors
| Name | Hex | Usage |
|------|-----|-------|
| BLP BG Orange | `#FCF5EE` | 웜톤 배경 |
| BLP BG Blue | `#EEF5FC` | 쿨톤 배경 |
| BLP BG Gray | `#F5F5F5` | 중성 배경 |
| BLP BG Green | `#B8E1D8` | 자연 배경 |
| BLP BG Purple | `#D9B8E1` | 창작 배경 |
| BLP BG Brown | `#D09C7B` | 어스톤 배경 |

---

## 2. Typography

```css
@import url("https://statics.goorm.io/fonts/GoormSans/v1.0.0/GoormSans.min.css");
@import url("https://statics.goorm.io/fonts/GoormSansCode/v1.0.1/GoormSansCode.min.css");
```

- **Primary Font**: `'Goorm Sans'`, `system-ui`, sans-serif
- **Code / Mono Font**: `'Goorm Sans Code'`, `monospace`
- **Heading Weight**: 700 (Bold)
- **Body Weight**: 400 (Regular)
- **Line Height**: 1.6 (body), 1.2 (heading)
- **Letter Spacing**: -0.02em (heading), 0 (body)

### Scale
| Level | Size | Weight | Usage |
|-------|------|--------|-------|
| H1 | 48px | 700 | 페이지 타이틀 |
| H2 | 36px | 700 | 섹션 타이틀 |
| H3 | 24px | 700 | 서브 섹션 |
| Body | 16px | 400 | 본문 |
| Caption | 12px | 400 | 보조 텍스트 |
| Code | 14px | 400 | 코드, 키보드 입력 |

---

## 3. Shape & Layout

### Border Radius
- **모든 요소**: `0px` (완전히 각진 모서리)
- 예외: 없음. 모든 것이 각져야 한다.

### Transparency
- **기본 요소 투명도**: `opacity: 0.97` 또는 `background: rgba(..., 0.97)`
- **배경 요소**: `opacity: 0.95`
- 투명도는 미세한 "디지털 질감"을 표현함

### Border
- **사용 금지**: 모든 요소에서 `border: 0` 또는 `border: none` 필수
- 요소 간 구분은 배경색, 그림자, 투명도, 여백으로만 처리

### Shadow System (테두리 대체 수단)
| State | Shadow | Description |
|-------|--------|-------------|
| Default | `none` | 그림자 없음 |
| Hover | `8px 8px 0px rgba({deep-color}, 0.35)` | 8px 우하단, 요소 색상의 딥 버전 |
| Active/Focus | `2px 2px 0px rgba({deep-color}, 0.5)` | 2px 우하단, 더 진한 딥 버전 |

> **절대 금기**: Hover/Focus 시 `transform: scale()` 사용 금지. 오직 `translateY(-8px)`만 사용.

### Spacing
- **Base Unit**: 8px
- **Component Padding**: 16px ~ 24px
- **Section Gap**: 64px ~ 96px
- **구분선**: `border` 사용 금지. 대신 2px 높이의 배경색 블록(div) 또는 여백으로 섹션 구분

---

## 4. Interaction & Motion

### Hover
```css
element {
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1),
              box-shadow 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: none; /* 필수 */
}
element:hover {
  transform: translateY(-8px);
  box-shadow: 8px 8px 0px rgba({deep-color}, 0.35);
}
```

### Active / Focus
```css
element:active,
element:focus-visible {
  transform: translateY(-2px);
  box-shadow: 2px 2px 0px rgba({deep-color}, 0.5);
}
```

---

## 5. Component Guidelines (No Border)

### Button
- 높이: 48px
- 패딩: 0 24px
- 배경: BLP Primary 색상 (opacity 0.97)
- 텍스트: BLP White, 16px, Weight 700
- 테두리: **없음** (`border: none`)
- Hover: translateY(-8px) + 8px 그림자
- Active: translateY(-2px) + 2px 그림자

### Card
- 패딩: 24px
- 배경: BLP White 또는 Paper/BG 색상 (opacity 0.97)
- 테두리: **없음**
- Hover: translateY(-8px) + 8px 그림자 (카드 테마 색상 기반)
- 카드 간 구분: 배경색 대비 + 그림자 + 여백(24px gap)

### Input
- 높이: 48px
- 패딩: 0 16px
- 배경: BLP White (opacity 0.97)
- 테두리: **없음**
- Focus: 2px 2px 0px 그림자 (BLP Blue 기반) + 배경색 미세 변화
- Placeholder: BLP Light Dark

### Badge / Tag
- 패딩: 4px 12px
- 배경: BLP Light 색상 (opacity 0.9)
- 텍스트: Ultra Deep 색상, 12px
- 테두리: **없음**

### Divider (구분선)
- `border-top` 사용 금지
- 대신: `height: 2px; background: var(--blp-light-dark); opacity: 0.3;` 형태의 div 사용

---

## 6. Background Specification (Halftone)

### 기본 원칙
BLP Main의 배경은 **이미지 또는 영상을 하프톤(dot pattern)으로 변환한 것**이 기본이다. 단색 도트 패턴은 폴백(Fallback)으로 사용한다.

### Image / Video Halftone (기본)
```
- Source: 이미지 파일 또는 Video 엘리먼트 프레임
- Processing: Canvas 2D getImageData -> 픽셀 샘플링 -> 도트 렌더링
- Dot Size: 픽셀 밝기(brightness)에 역비례. 어두운 영역 = 큰 도트, 밝은 영역 = 작은 도트/생략
- Dot Color: 원본 픽셀 색상을 BLP 파레트로 양자화하거나, 원본 그대로 사용
- Dot Spacing: 16px ~ 24px (고정 그리드)
- Animation (영상): 프레임 단위로 픽셀 데이터 갱신, 도트 크기/색상 실시간 변화
- 배열: 이미지/영상에 따라 고정. 상호작용(마우스, 스크롤, 강조) 시에만 왜곡 허용
- Opacity: 0.15 ~ 0.35 (콘텐츠 가독성 보장)
- Background Base: BLP BG Gray (#F5F5F5) 또는 BLP Paper Blue (#F4F8FC)
```

### Minimal Dot Background (폴백)
이미지/영상 소스가 없을 때 사용.
```
- Source: 없음 (단색/그라데이션 없음)
- Dot Size: 사인파 기반 가변 (3px ~ 8px, 4s period)
- Color: BLP Primary 색상 순환 (Blue -> Purple -> Red -> Green -> Yellow, 20s loop)
- Dot Position: 고정된 대각선 그리드. 시간에 따라 이동하지 않음
- 배열 변화: 사용자 상호작용 시에만 허용
- Opacity: 0.15 ~ 0.25
```

### Dot Behavior Rules

| 속성 | 기본 상태 | 허용 여부 |
|------|----------|----------|
| **색상 변화** | 시간/프레임 흐름에 따라 순환 | ✅ OK |
| **점 크기 변화** | 밝기 기반 또는 사인파 기반 가변 | ✅ OK |
| **배열(위치) 변화** | **절대 고정**. 시간/자동 애니메이션으로 이동 금지 | ❌ 절대 금지 |
| **배열 변화** | 사용자 상호작용(스크롤, 마우스, 클릭, 강조 등) 시에만 허용 | ✅ OK |

> **핵심 원칙**: 가만히 있는 상태에서 배열이 알아서 변하는 것은 불필요한 혼란을 야기함. 배열 변화는 반드시 "의도된 상호작용"의 결과여야 한다.

---

## 7. Do's and Don'ts

### ✅ Do
- 모든 모서리는 완전히 각지게 유지 (`border-radius: 0`)
- 투명도는 0.95 ~ 0.97 범위에서 미세 조정
- 그림자는 항상 우하단 (8px 8px 또는 2px 2px), blur 없이 offset만
- Hover 시 translateY(-8px) 사용
- Active 시 translateY(-2px) 사용
- **테두리는 절대 사용하지 않음** — 배경색/그림자/투명도로 구분
- **배경은 이미지/영상 하프톤 변환이 기본**
- **Halftone 배열은 상호작용 시에만 변화** — idle 상태에서는 고정

### ❌ Don't
- `border-radius` 사용 금지
- `border` 속성 사용 금지 (어떤 경우에도)
- Hover/Focus 시 `transform: scale()` 사용 금지
- 그림자에 blur 효과 사용 금지 (spread만 사용, offset 그림자)
- 요소 크기 변경 없이 위치/그림자로만 피드백 제공
- **Halftone 배열이 idle 상태에서 자동으로 변화** — 시간 흐름만으로 위치 이동 금지
- **단색 도트를 기본 배경으로 사용** — 이미지/영상 하프톤이 우선

---

*BLP Main v1.0 — No borders, only halftone dreams.*
