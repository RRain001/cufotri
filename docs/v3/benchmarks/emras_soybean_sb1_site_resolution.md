# EMRAS soybean SB1 site resolution

## Decision

```text
COORDINATE_STATUS = PROVISIONAL_INSTITUTIONAL_LOCATION
SITE_COORDINATE = 36.425000 N, 127.373611 E
TIMEZONE = Asia/Seoul
UTC_OFFSET_ON_2001_07_02 = +09:00
EVIDENCE_STRENGTH = C
EXACT_EXPERIMENT_SITE = FALSE
FIVE_POINT_ERA5_SPATIAL_SENSITIVITY = REQUIRED
```

The IAEA meeting record states that the soybean experiment data were collected
at the Korea Atomic Energy Research Institute. The public scenario report says
that the pots were placed in an open field and that a meteorological tower was
near the planting area, but it supplies no coordinate. KAERI's official
Daejeon headquarters page gives the institution address in Yuseong-gu. A KAERI
environmental report places the institute and its meteorological tower in
Deokjin-dong. A peer-reviewed paper reports a Deokjin site in Yuseong-gu at
36 deg 25 min 30 sec N, 127 deg 22 min 25 sec E. That point is used only as an
institutional-area proxy.

This coordinate is not a confirmed experiment plot or measurement coordinate.
It must never be upgraded to evidence grade A or described as exact without a
primary experiment source.

## Sources

- IAEA, [4th EMRAS Tritium and C-14 Working Group report](https://www-ns.iaea.org/downloads/rw/projects/emras-4th-tritium-wg-final-report.pdf).
- KAERI, [Daejeon Headquarters - Contact and Location](https://kaeri.re.kr/board?menuId=MENU00737).
- KAERI, [2019 environmental radiation assessment report listing the Deokjin-dong meteorological tower](https://www.kaeri.re.kr/env/board/view?boardStyle=&categoryId=&continent=&country=&linkId=8393&menuId=MENU00393&no1=11&pageNum=1&rowCnt=10&schText=&schType=0&schYear=).
- Youn et al. (2007), [SNU-AMS Radiocarbon Date List IV](https://journals.uair.arizona.edu/index.php/radiocarbon/article/viewFile/3022/2780).

## ERA5 points

| Scenario | Latitude | Longitude |
|---|---:|---:|
| CENTRE | 36.425000 | 127.373611 |
| NORTH_0P25 | 36.675000 | 127.373611 |
| SOUTH_0P25 | 36.175000 | 127.373611 |
| EAST_0P25 | 36.425000 | 127.623611 |
| WEST_0P25 | 36.425000 | 127.123611 |

Timezone conversion is performed with the IANA `Asia/Seoul` zone. Both local
and UTC timestamps and the explicit offset are retained.
