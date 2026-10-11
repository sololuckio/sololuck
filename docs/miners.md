# Bitcoin (SHA-256) miner specs: verified

**Researched:** 11 October 2026

Every number comes from the maker's own website, manual, press release or official GitHub page. The links are next to each model.
There are no live readings here.

**Lower J/TH = better.** J/TH (joules per terahash) is how much electricity a miner needs for each unit of work. It's the number that decides running cost.

Every current Bitcoin (SHA-256) miner from the main makers, as of 11 October 2026.
There is one table per maker, sorted from best efficiency (lowest J/TH) to worst.

**How to read these tables**

- **Cooling:**
  - **air** means fans.
  - **hydro** means water-cooled.
  - **immersion** means the miner sits in a tank of cooling liquid.
  - Hydro and immersion machines need special setups and are not for home use.
- **A range** (for example 244–280) means the maker sells or rates the machine across that range.
- **Two power numbers** (for example 7200 / 10,000) mean a normal mode and a high-performance mode.
- **(calc.)** means power divided by hashrate, worked out here because the maker doesn't print it.
- **Announced / pre-order** means you can't buy one that ships today.
- Makers usually allow about ±5% on hashrate and ±5–10% on power.

## Best picks

| | Machine | Why |
|---|---|---|
| **Most efficient overall** | Bitmain **S23 XP Hyd.**: 600 TH/s, 8.9 J/TH | Water-cooled. Pre-order only, ships from November 2026. Next best: Bitdeer SealMiner A4 Ultra Hydro at 9.45 J/TH. |
| **Most efficient air-cooled** | Bitdeer **SealMiner A4 Pro Air**: 336 TH/s, 10.9 J/TH | Pre-order. Close behind: Bitmain **S23** at 305 TH/s and 11 J/TH, which ships from Q3 2026 and is sold out. |
| **Most efficient air-cooled you can buy now** | MicroBT **M70S+**: 244–280 TH/s, 12.5 J/TH | Launched December 2025. Bitdeer's A3 Pro Air matches it at 12.5 J/TH but is pre-order. |
| **Best home / quiet miner** | Canaan **Avalon Q**: 90 TH/s, 18.6 J/TH | Normal wall socket, 45 dB at its quietest. |
| **Best tiny miner** | **NerdQAxe++**: ~4.8 TH/s, ~15.8 J/TH | The most efficient of the small open-source boards with a published rating. |

## Bitmain Antminer

Sources are Bitmain's own shop (shop.bitmain.com / m.bitmain.com), support site (support.bitmain.com) and news pages.

| Model | Cooling | Hashrate (TH/s) | Power (W) | J/TH | Released | Source |
|---|---|---|---|---|---|---|
| S23 XP Hyd. | hydro | 600 | 5340 | 8.9 | Launched Aug 2026. **Pre-order**, ships from Nov 2026 | [shop](https://shop.bitmain.com/product/detail?pid=000202608201636197889T3Y4SxC0660) · [news](https://www.bitmain.com/news-detail/wdms-global-2026-successfully-held-in-hong-kong-463) |
| S23 Hyd. | hydro | 580 | 5510 | 9.5 | Launched May 2025. Shipping in 2026, sold out | [shop](https://m.bitmain.com/product/detail?pid=00020250525151230946ki4IicUp06D6) · [news](https://www.bitmain.com/news-detail/wdms-2025-successfully-held-in-las-vegas-396) |
| U3S23H (3U rack) | hydro | 1160 | 11020 | 9.5 | Ships from Q3 2026, sold out | [shop](https://m.bitmain.com/product/detail?pid=00020250707194812615L4HTKEMY064E) |
| S23e U2H (2U rack) | hydro | 865 | 8650 | 10 | Launched Jan 2026, ships Q2 2026 | [news](https://www.bitmain.com/news-detail/bitmain-launches-antminer-s23e-u2h-432) |
| S21 XP+ Hyd. | hydro | 480 | 5280 | 11.0 | Current batch ships Oct 2026 | [shop](https://shop.bitmain.com/product/detail?pid=000202509301221500115U8GHT3J0604) |
| **S23** | air | 305 | 3355 | 11 | Ships from Q3 2026, sold out | [shop](https://shop.bitmain.com/product/detail?pid=00020260423220459308u20qQN420641) |
| S21j XP Hyd. | hydro | 495 | 5940 | 12.0 | Ships from Oct 2026 | [shop](https://shop.bitmain.com/product/detail?pid=00020251222142202843CFQByJe40662) |
| S21 XP Hyd. | hydro | 473 | 5676 | 12 | First batch Dec 2024 | [shop](https://shop.bitmain.com/product/detail?pid=00020260818135755111661061ap05FD) · [spec](https://support.bitmain.com/hc/en-us/articles/34523540504857) |
| U3S21EXPH (rack) | hydro | 860 | 11180 | 13 | In use at a customer site by Jul 2025 | [news](https://www.bitmain.com/news-detail/bitmain-and-abtc-launch-large-scale-deployment-of-antminer-u3s21exph-421) |
| S21e XP Hyd. | hydro | 430 | 5590 | 13 | Ships from Nov 2025 | [shop](https://m.bitmain.com/product/detail?pid=00020241116122545545VogaKj7z06E5) |
| S21 XP Imm. (normal / high mode) | immersion | 300 / 380 | 4050 / 5700 | 13.5 / 15.0 | Shown Oct 2024 | [shop](https://shop.bitmain.com/product/detail?pid=00020260910170551697xvID9SCf06AD) |
| **S21 XP** | air | 270 | 3645 | 13.5 | Ships from Dec 2024 | [shop](https://shop.bitmain.com/product/detail?pid=00020240628121614609dw7bmIit06FD) · [spec](https://support.bitmain.com/hc/en-us/articles/35383015643673) |
| S21+ Hyd. | hydro | 358 | 5370 | 15 | Launched Oct 2024 | [shop](https://shop.bitmain.com/product/detail?pid=00020260924145421522Rn7yNQxW06D1) |
| S21 Pro | air | 234 | 3510 | 15 | not published | [spec](https://support.bitmain.com/hc/en-us/articles/31321354157593) |
| S21 Hyd. (two grades) | hydro | 335 / 319 | 5360 / 5104 | 16.0 | Announced Oct 2023, shipping Aug 2024 | [spec](https://support.bitmain.com/hc/en-us/articles/26824251926681) · [shop](https://shop.bitmain.com/product/detail?pid=00020240718151523125gE0aB5Es065D) |
| S21 Imm. (normal mode) | immersion | 215 (shop) / 239 (spec page) | 3440 / 3824 | 16.0 | Spec page dated Jul 2024 | [shop](https://shop.bitmain.com/product/detail?pid=000202412141809131002JB8yYL3062E) · [spec](https://support.bitmain.com/hc/en-us/articles/35746238371097) |
| S21+ | air | 216 | 3564 | 16.5 | Launched Oct 2024, shipped Q1 2025 | [shop](https://shop.bitmain.com/product/detail?pid=00020241029165519141lBFc0bx8068E) · [news](https://www.bitmain.com/news-detail/bitmain-launches-the-antminer-s21-series-358) |
| S21e Hyd. | hydro | 288 | 4896 | 17 | not published | [shop](https://shop.bitmain.com/product/detail?pid=00020250415165203914Mlh3dx1h06BB) |
| S21e Hyd. (hosted version) | hydro | 310 | 5270 | 17 | not published | [shop](https://shop.bitmain.com/product/detail?pid=00020250807171014054O9Lfsoki06DF) |
| **S21** | air | 200 | 3500 | 17.5 | Announced Oct 2023, first batch Jan 2024 | [spec](https://support.bitmain.com/hc/en-us/articles/23794895251609) · [news](https://www.bitmain.com/news-detail/bitmain-releases-antminer-s21-hyd--s21-with-an-outstanding-energy-efficiency-of-16-jt-300) |
| S21 Imm. (high mode) | immersion | 301 | 5569 | 18.5 | same unit as normal mode above | [spec](https://support.bitmain.com/hc/en-us/articles/35746238371097) |
| S19 XP+ Hyd. | hydro | 279 | 5301 | 19 | not published | shop listing (sold out), no spec page |
| T21 (normal / high mode) | air | 190 / 233 | 3610 / 5126 | 19.0 / 22.0 | Spec page dated Nov 2023 | [spec](https://support.bitmain.com/hc/en-us/articles/24967960325785) |
| S19 XP Hyd. | hydro | 257 | 5346 | 20.8 | not published | [spec](https://support.bitmain.com/hc/en-us/articles/36035119865113) |
| S19j XP | air | 151 | 3247 | 21.5 | not published | [spec](https://support.bitmain.com/hc/en-us/articles/20090196798361) |
| S19 XP | air | 141 | 3031.5 | 21.5 (calc.) | not published | [spec](https://support.bitmain.com/hc/en-us/articles/8906244096409) |
| S19e XP Hyd. (two grades) | hydro | 251 / 240 | 5522 / 5280 | 22 | not published | [spec](https://support.bitmain.com/hc/en-us/articles/32875494202265) |
| S19k Pro | air | 120 / 115 / 110 / 105 | 2760 / 2645 / 2530 / 2415 | 23 | Spec page posted Oct 2023 | [spec](https://support.bitmain.com/hc/en-us/articles/23833956049049) |
| S19 Pro++ | air | 125 / 120 / 115 | 3250 / 3120 / 2990 | 26 (calc.) | not published | [spec](https://support.bitmain.com/hc/en-us/articles/36861394055065) |
| S19 Pro+ Hyd. | hydro | 191 | 5252.5 | 27.5 | not published | [shop](https://shop.bitmain.com/product/detail?pid=00020221229153045195XzfP62rE069C) |
| S19j Pro | air | 104 | 3068 | 29.5 | not published | [spec](https://support.bitmain.com/hc/en-us/articles/900006762746) |

**Notes:**
- **Bitmain's own pages contradict each other in places.**
  - The S21+ Hyd. was launched at 319 TH/s, but the shop now says 358 TH/s.
  - For the S21 Imm., the shop and the spec page give different normal-mode numbers.
- **Not on Bitmain's site:**
  - A reseller "S23 318T". Bitmain lists the S23 at 305 TH/s, so the 318 figure is unverified.
  - No air-cooled S21e and no S23 immersion model.
- **Partly read pages:** the S19j Pro, S19k Pro and S19 Pro++ pages didn't load in full, so their numbers come from Bitmain's own article text. They may list more versions.
- **Shop listing only:** the S23e U2H, U3S21EXPH and S19 XP+ Hyd. have no spec page.

## MicroBT Whatsminer

Sources are MicroBT's own product manuals, listed on [whatsminer.com/product_manual](https://www.whatsminer.com/src/views/product_manual.html).
The manuals call the figures "prototype data for reference only".
Release dates come from MicroBT's news pages: the M70 series launched 8 December 2025, the M60S++ 10 December 2024, the M60S+ 28 July 2024 and the M60 series 25 October 2023.

Model names are grouped where MicroBT gives identical specs. The letter after the number is the cooling type:
- **M70S / M60S** = air
- **M73 / M63** = water
- **M76 / M66** = immersion
- **M7A / M7B / M7D** (and M6A / M6B / M6D) = water-cooled versions built for hot-water outlets: 70 °C, 90 °C and 65 °C

| Model | Cooling | Hashrate (TH/s) | Power (W) | J/TH | Released | Source (manual) |
|---|---|---|---|---|---|---|
| **M70S+** | air | 244–280 | 3140–3500 | 12.5 | Dec 2025 | [M70S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM70S%2B_1775811512444.pdf) |
| M73S+ / M7AS+ / M7BS+ | hydro | 540–600 | 7200 / 10,000 | 12.5 | Dec 2025; M7A/M7B manuals dated Feb–Apr 2026 | [M73S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM73S%2B_1775811616409.pdf) · [M7AS+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7AS%2B_1778123592479.pdf) · [M7BS+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7BS%2B_1778138167731.pdf) |
| M76S+ | immersion | 390–440 | 5200 / 7000 | 12.5 | Dec 2025 | [M76S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM76S%2B_1775811816753.pdf) |
| M70S | air | 226–258 | 3140–3500 | 13.5 | Dec 2025 | [M70S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM70S_1775811411924.pdf) |
| M73S / M7AS / M7BS | hydro | 500–552 | 7200 / 10,000 | 13.5 | Dec 2025; M7A/M7B manuals Feb–Apr 2026 | [M73S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM73S_1775811575292.pdf) · [M7AS](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7AS_1778123567731.pdf) · [M7BS](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7BS_1778138159856.pdf) |
| M7DS | hydro | 638–702 | 9200 | 13.5 | manual Feb 2026 | [M7DS](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7DS_1777449383882.pdf) |
| M76S | immersion | 362–406 | 5200 / 7000 | 13.5 | Dec 2025 | [M76S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM76S_1775811795246.pdf) |
| M70 | air | 214–236 | 3140–3500 | 14.5 | Dec 2025 | [M70](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM70_1775811281512.pdf) |
| M73 / M7A / M7B | hydro | 470–526 | 7200 / 10,000 | 14.5 | Dec 2025; M7A/M7B manuals Feb–Apr 2026 | [M73](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM73_1775811562514.pdf) · [M7A](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7A_1778123120619.pdf) · [M7B](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7B_1778138140482.pdf) |
| M7D | hydro | 594–652 | 9200 | 14.5 | manual Feb 2026 | [M7D](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM7D_1777449401987.pdf) |
| M76 | immersion | 336–374 | 5200 / 7000 | 14.5 | Dec 2025 | [M76](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM76_1775811690545.pdf) |
| M60S++ | air | 200–226 | 3230–3570 | 15.5 | Dec 2024 | [M60S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM60S%2B%2B_1760948259244.pdf) |
| M63S++ / M6AS++ / M6BS++ | hydro | 434–478 | not published (10 kW input); M6BS++: 7200 / 10,000 | 15.5 | Dec 2024; M6A/M6B manuals Feb–Apr 2026 | [M63S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM63S%2B%2B_1766127946760.pdf) · [M6AS++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM6AS%2B%2B_1778122989034.pdf) · [M6BS++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM6BS%2B%2B_1778138098334.pdf) |
| M6DS++ | hydro | 556–610 | 9200 | 15.5 | manual Feb 2026 | [M6DS++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM6DS%2B%2B_1775811194720.pdf) |
| M66S++ | immersion | 314–356 | not published | 15.5 | Dec 2024 | [M66S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM66S%2B%2B_1760947860007.pdf) |
| M60S+ | air | 190–210 | 3230–3570 | 17 | Jul 2024 | [M60S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM60S%2B_1760948749607.pdf) |
| M63S+ / M6AS+ / M6BS+ | hydro | 390–450 | not published (10 kW input); M6BS+: 7200 / 10,000 | 17 | Jul 2024; M6A/M6B manuals Feb–Apr 2026 | [M63S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM63S%2B_1766127923007.pdf) · [M6AS+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM6AS%2B_1778122981654.pdf) · [M6BS+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM6BS%2B_1778135740420.pdf) |
| M6DS+ | hydro | 504–556 | 9200 | 17 | manual Feb 2026 | [M6DS+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM6DS%2B_1775811205004.pdf) |
| M66S+ | immersion | 280–318 | not published | 17 | Jul 2024 | [M66S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM66S%2B_1760947640639.pdf) |
| M60S | air | 170–186 | 3145–3441 | 18.5 | Oct 2023 | [M60S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM60S_1760948331396.pdf) |
| M63S / M65S | hydro | 370–400 | not published (10 kW input) | 18.5 | Oct 2023 (M65S manual Oct 2024) | [M63S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM63S_1766127899887.pdf) · [M65S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM65S_1766127986147.pdf) |
| M66S | immersion | 270–298 | not published | 18.5 | Oct 2023 | [M66S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM66S_1760947624158.pdf) |
| M60 | air | 150–172 | 2985–3422 | 19.9 | Oct 2023 | [M60](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM60_1760948365793.pdf) |
| M63 | hydro | 334–366 | not published (10 kW input) | 19.9 | Oct 2023 | [M63](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM63_1766127870170.pdf) |
| M64 | hydro | 180–206 | not published (5 kW input) | 19.9 | manual Oct 2024 | [M64](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM64_1766127966651.pdf) |
| M66 | immersion | 240–276 | not published | 19.9 | Oct 2023 | [M66](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM66_1760947600855.pdf) |
| M50S++ | air | 138–158 | 3036–3476 | 22 | M50 series launched Apr 2022 | [M50S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM50S%2B%2B_1760947002245.pdf) |
| M53S++ / M54S++ | hydro | 310–328 / 168–190 | not published (10 kW / 5 kW input) | 22 | manuals Oct 2024 | [M53S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM53S%2B%2B_1766127852528.pdf) · [M54S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM54S%2B%2B_1766127773829.pdf) |
| M56S++ | immersion | 222–236 | not published | 22 | manual Oct 2024 | [M56S++](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM56S%2B%2B_1760947455408.pdf) |
| M50S+ / M53S+ / M56S+ | air / hydro / immersion | 130–142 / 282–298 / 206–224 | 3120–3408 (air); others not published | 24 | manuals Oct 2024 | [M50S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM50S%2B_1760946979662.pdf) · [M53S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM53S%2B_1766127791450.pdf) · [M56S+](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM56S%2B_1760948833167.pdf) |
| M50S / M53S / M56S | air / hydro / immersion | 120–134 / 260–274 / 194–220 | 3120–3484 (air); others not published | 26 | manuals Oct 2024 | [M50S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM50S_1760946474127.pdf) · [M53S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM53S_1766127815577.pdf) · [M56S](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM56S_1760948808208.pdf) |
| M50 / M53 / M56 | air / hydro / immersion | 110–130 / 226–250 / 168–194 | 3190–3770 (air); others not published | 29 | manuals Oct 2024 | [M50](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM50_1745223329978.pdf) · [M53](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM53_1766127833846.pdf) · [M56](https://aws-microbt-com-bucket.s3.us-west-2.amazonaws.com/WhatsMinerM56_1760948773966.pdf) |
| M30S++ | air | 102–104 | 3224 | 31 | not published | [MicroBT shop](https://shop.whatsminer.com/products/details/52) |
| M30S+ | air | 100 | not published | 34 | not published | [MicroBT shop](https://shop.whatsminer.com/products) |

**Notes:**
- **Water-cooled power.** For most water-cooled models MicroBT gives only the power-supply input rating (10 kW or 5 kW), not the actual draw. The immersion manuals leave power blank.
- **Unverified models.** Resellers sell an M72/M72S, M78/M78S and M79/M79S, but MicroBT publishes no manual for them, so they're left out.
- **Shop vs manual.** For a few older models (M63S, the M50 family) MicroBT's shop shows slightly different numbers from the manuals. This table uses the manuals.
- **microbt.com** no longer has product pages. MicroBT's specs now live on whatsminer.com.

## Canaan Avalon

Sources are Canaan's own shop (shop.canaan.io), its website (canaan.io) and Canaan press releases.

| Model | Cooling | Hashrate (TH/s) | Power (W) | J/TH | Released | Source |
|---|---|---|---|---|---|---|
| **A16XP-300T** | air | 300 | 3850 | 12.8 | Launched Oct 2025. **Pre-order**, ships from Q2 2026, sold out | [shop](https://shop.canaan.io/products/avalon-miner-a16xp-300t) · [press](https://www.prnewswire.com/news-releases/canaan-inc-unveils-next-gen-avalon-a16-series-bitcoin-mining-machine-featuring-breakthrough-asic-chip-302596838.html) |
| A16-282T | air | 282 | 3900 | 13.8 | Launched Oct 2025. **Pre-order**, ships from May 2026 | [shop](https://shop.canaan.io/products/avalon-miner-a16-282t) |
| A15Pro+ 240T | air | 240 | 3720 | 15.5 | not published (in stock) | [shop](https://shop.canaan.io/products/avalon-miner-a15pro-240t) |
| A1566HA-500T | hydro | 500 | 8064 | 16.8 listed (16.1 calc.) | not published (in stock) | [shop](https://shop.canaan.io/products/avalon-miner-a1566ha-500t) |
| A15Pro-221T | air | 221 | 3662 | 16.8 | Nov 2024 | [shop](https://shop.canaan.io/products/avalon-miner-a15pro-221t) · [press](https://www.prnewswire.com/news-releases/canaan-upgraded-avalon-miner-a15-series-with-superior-performance-302299656.html) |
| A1566HA-460T | hydro | 460 | 8200 | 17.8 | Ships Dec 2025 | [shop](https://shop.canaan.io/products/avalon-miner-a1566ha-460t) |
| A1566I-273T / 270T | immersion (Canaan's page doesn't say; the "I" suggests it) | 273 / 270 | 4500 (detail page) or 4959 (shop list) | 17.8 | not published | [273T](https://shop.canaan.io/products/avalon-miner-a1566i-273t) · [270T](https://shop.canaan.io/products/avalon-miner-a1566i-270t) |
| A15XP-209T | air | 209 | 3720 or 3667 (pages differ) | 17.8 | Nov 2024, now in clearance | [shop](https://shop.canaan.io/products/avalon-miner-a15xp-209t) · [A15 page](https://www.canaan.io/miner/A15/) |
| **Avalon Q** (home) | air | 90 | 1674 (shop); modes 800 / 1300 / 1600 | 18.6 | Mar 2025 | [shop](https://shop.canaan.io/products/avalon-q-1) · [page](https://www.canaan.io/minerq/) |
| A15-200T | air | 200 | 3760 | 18.8 | Shipped Sep 2025, now clearance | [shop](https://shop.canaan.io/products/avalon-miner-a15-200t) |
| A15 (series page) | air | 194 or 185 (pages differ) | 3647 | 18.8 | Nov 2024 | [A15 page](https://www.canaan.io/miner/A15/) |
| **Avalon Mini 3** (home) | air | 37.5 | 800 max | 21.3 | Jan 2025 | [shop](https://shop.canaan.io/products/avalon-mini-3) · [page](https://www.canaan.io/mini3/) |
| A14XP-154T / 152T / 150T | air | 154 / 152 / 150 | 3500 | 21.5 listed (22.7–23.3 calc.) | Futures from Dec 2025 | [154T](https://shop.canaan.io/products/avalon-miner-a14xp-154t) · [152T](https://shop.canaan.io/products/avalon-miner-a14xp-152t) · [150T](https://shop.canaan.io/products/avalon-miner-a14xp-150t) |
| A1466 (series page) | air | 162 | 3500 (power-supply figure) | 23.3 listed (21.6 calc.) | not published | [A14 page](https://www.canaan.io/miner/A14/) |
| **Avalon Nano 3S** (home) | air | 6 | 140 max | 23.3 (calc.) | Jan 2025 | [shop](https://shop.canaan.io/products/avalon-nano-3s-1) · [page](https://www.canaan.io/nano3s/) |
| A1446 (series page) | air | 133 | 3600 (power-supply figure) | 27.1 | not published | [A14 page](https://www.canaan.io/miner/A14/) |
| A1366I-122T / 119T | immersion | 122 / 119 | 3570 | 29.2 / 30.0 | not published | [122T](https://shop.canaan.io/products/avalon-miner-a1366i-122t-immersion-cooling) · [119T](https://shop.canaan.io/products/avalon-miner-a1366i-119t-immersion-cooling) |
| A1366I-128T / 125T | immersion | 128 / 125 | 3750 max | 29.3 / 30.0 (calc.) | not published | [128T](https://shop.canaan.io/products/avalon-miner-a1366i-128t-immersion-cooling) · [125T](https://shop.canaan.io/products/avalon-miner-a1366i-125t-immersion-cooling) |
| A1326 (series page) | air | 109 | 3520 | 32.3 (calc.) | not published | [A13 page](https://www.canaan.io/miner/A13/) |
| A16 hot-water-cooled models | hydro | not published | not published | not published | **Announced** Sep 2026 | [press](https://www.prnewswire.com/news-releases/canaan-inc-reports-unaudited-second-quarter-2026-financial-results-302872107.html) |
| New Avalon home heaters (no names yet) | not published | not published | not published | not published | **Announced** for winter 2026 | same press release |

**Notes:**
- **Canaan's own pages often disagree.** Sometimes the J/TH they print doesn't match their own power and hashrate. Both figures are shown where that happens.
- **No new home miner since the Avalon Q.** Canaan's September 2026 release still lists only the Nano 3S, Mini 3 and Avalon Q.

## Bitdeer SealMiner

Sources are Bitdeer's own shop (bitdeer.com/shop), announcements and investor news (ir.bitdeer.com).

| Model | Cooling | Hashrate (TH/s) | Power (W) | J/TH | Released | Source |
|---|---|---|---|---|---|---|
| **A4 Ultra Hydro** | hydro | 886 | 8372.7 | 9.45 | Launched Apr 2026. Mass production since May 2026; **pre-order** in the shop | [news](https://ir.bitdeer.com/news-releases/news-release-details/bitdeer-launches-sealminer-a4-series-bitcoin-mining-rigs) · [shop](https://www.bitdeer.com/shop/product/P260328000003) |
| A4 Pro Hydro | hydro | 680 | 7412 | 10.9 | Apr 2026, **pre-order** | [shop](https://www.bitdeer.com/shop/product/P260328000002) |
| **A4 Pro Air** | air | 336 | 3662.4 | 10.9 | Apr 2026, **pre-order** | [shop](https://www.bitdeer.com/shop/product/P260328000001) |
| A3 Pro Hydro | hydro | 660 (630–690) | 8250 (7875–8625) | 12.5 | Sep 2025, in stock | [announcement](https://www.bitdeer.com/announcement/sealminer-a3-series-is-here--next-gen-mining-with-higher-hashrate-and-efficiency) · [shop](https://www.bitdeer.com/shop/product/P260225000004) |
| A3 Pro Air | air | 290 (260–320) | 3625 (3250–4000) | 12.5 | Sep 2025, **pre-order** | [shop](https://www.bitdeer.com/shop/product/P250619000003) |
| A3 Hydro | hydro | 500 (460–540) | 6750 (6210–7290) | 13.5 | Sep 2025, in stock | [shop](https://www.bitdeer.com/shop/product/P260225000003) |
| A3 Air | air | 260 (240–280) | 3640 (3360–3920) | 14 | Sep 2025, **pre-order** | [shop](https://www.bitdeer.com/shop/product/P250617000001) |
| A2 Pro Hydro | hydro | 500–530 | 7450–7900 | 14.9 | Mar 2025, sold out | [news](https://ir.bitdeer.com/news-releases/news-release-details/bitdeer-launches-sealminer-a2-pro-bitcoin-mining-machines) · [shop](https://www.bitdeer.com/shop/product/P251110000002) |
| A2 Pro Air | air | 255–270 (shop: 260) | 3790–4050 (shop: 3874) | 14.9 | Mar 2025, sold out | [shop](https://www.bitdeer.com/shop/product/P260105000001) |
| A2 Hydro | hydro | 446 | 7359 | 16.5 | 2024, sold out | [shop](https://www.bitdeer.com/shop/product/P241105000002) |
| A2 | air | 226 | 3729 | 16.5 | 2024, sold out | [shop](https://www.bitdeer.com/shop/product/P250414000002) |

**Notes:**
- **A4 Ultra Hydro high mode.** Bitdeer's own video shows some A4 Ultra Hydro units running at up to 1,000 TH/s at 10 J/TH. It's not in the spec sheet.
- **A1.** It was never sold; it was used only in Bitdeer's own mines.

## Auradine Teraflux (now Velaura AI)

Sources are Auradine/Velaura datasheets (velaura.ai) and press releases.
Auradine renamed itself **Velaura AI** in March 2026. News reports (not the company) say it is selling off stock, so the next-generation machines may never ship.
Its product page states a 500-unit minimum order.

| Model | Cooling | Hashrate (TH/s) | Power (W) | J/TH | Released | Source |
|---|---|---|---|---|---|---|
| Next-gen Teraflux (eco / normal mode) | hydro | 600 / 900 | 5880 / 9900 (calc.) | 9.8 / 11 | **Announced** Nov 2025 | [press](https://www.prnewswire.com/news-releases/auradine-advances-teraflux-btc-mining-product-portfolio-delivering-category-leading-energy-efficiency-at-9-8-jth-with-breakthrough-tco-302612073.html) |
| Next-gen Teraflux (eco / normal mode) | immersion | 240 / 360 | 2352 / 3852 (calc.) | 9.8 / 10.7 | **Announced** | same |
| Next-gen Teraflux (eco / normal mode) | air | 240 / 310 | 2472 / 3410 (calc.) | 10.3 / 11 | **Announced** | same |
| AH3880 (eco / mid / turbo mode) | hydro | 400 / 500 / 600 | 5720 / 7900 / 10,500 (calc.) | 14.3 / 15.8 / 17.5 | Mar 2025 | [datasheet](https://velaura.ai/wp-content/uploads/2025/09/Teraflux™-AH3880-Data-Sheet.pdf) |
| AT2880 (normal / turbo mode) | air | 180 / 270 | 2880 / 4860 (calc.) | 16 / 18 | Jul 2024 | [datasheet](https://velaura.ai/wp-content/uploads/2025/09/Teraflux™-AT2880-Data-Sheet.pdf) |
| AI3680 (normal / turbo mode) | immersion | 250 / 365 | 4000 / 6935 (calc.) | 16 / 19 | Jul 2024 | [datasheet](https://velaura.ai/wp-content/uploads/2025/02/Teraflux™-AI3680-Data-Sheet.pdf) |

**Note:** Auradine's 2024 launch release gave different numbers from the current datasheets. This table uses the datasheets.

## Other makers

| Maker and model | Cooling | Hashrate (TH/s) | Power (W) | J/TH | Released | Source |
|---|---|---|---|---|---|---|
| **Block, Proto Rig** (9 hashboards) | air ("immersion ready") | up to 819 | up to 12,000 at the wall | as low as 14.1 | Aug 2025 | [proto.xyz](https://proto.xyz/products/rig) |
| **Fluminer T3** (home / small farm) | air | 105 | 1650 | 15 stated (15.7 calc.) | 2025, "in production" | [fluminer.com](https://fluminer.com/en/product_detail.aspx?cid=390&id=52) |
| **FutureBit Apollo III** (eco / turbo mode) | air | ~10–12 / ~16–18 | 150 / 375 (at the board) | "down to 13" / ~21–23 (calc.) | **Pre-order**, ship date not published | [futurebit.io](https://www.futurebit.io/apollo-3) |
| **BGIN** (maker of ICERIVER), BT1-chip miner | not published | not published | not published | not published | **Announced**: chip working Mar 2026, no product yet | [SEC filing](https://www.sec.gov/Archives/edgar/data/1945565/000121390026028429/ea028184401ex99-1.htm) |

**Checked and left out:**
- **Ebang:** no current Bitcoin model.
- **Goldshell / Intchains:** they make miners for other coins only.
- **Braiins BMM, Magicminer, Lucky Miner:** small home units built on Bitmain chips, in the same class as the Bitaxe.

## Open-source home miners (Bitaxe and NerdQAxe families)

Sources are the designers' GitHub pages and the official firmware.
Most designers don't publish a rating. In that case, "at stock" is what the official firmware expects at its default settings, and the power is the firmware's factory self-test target.
No release dates are published.

| Model | Chip | Hashrate (TH/s) | Power (W) | J/TH | Power input | Source |
|---|---|---|---|---|---|---|
| Bitaxe NajaDuo (1201), **untested prototype** | 2 × BM1373 | 4.40 at stock | 50 | 11.4 (calc.) | 12 V | [repo](https://github.com/bitaxeorg/naja-duo) |
| **NerdQAxe++** | 4 × BM1370 | ~4.8 | ~76 | ~15.8 | 12 V | [repo](https://github.com/shufps/qaxe) |
| NerdHaxe-γ (Patsch91) | 6 × BM1370 | ~7.35 | 120–125 at the wall | 16.3–17.0 (calc.) | 12 V, at least 15 A | [repo](https://github.com/Patsch91/NerdHAXE-Gamma) |
| Bitaxe GammaHex (1300) | 6 × BM1370 | 8.45 at stock | 140 | 16.6 (calc.) | 12 V | [repo](https://github.com/bitaxeorg/BitaxeGammaHex) |
| **Bitaxe GammaTurbo** (801) | 2 × BM1370 | 2.14 at stock | 36 | 16.8 (calc.) | 12 V | [repo](https://github.com/bitaxeorg/BitaxeGT) |
| **Bitaxe Gamma** (601 / 602 / 603) | 1 × BM1370 | ~1.2 (designer); 1.07 at stock | 19 (601) / 22 (602, 603) | 17.7 / 20.5 (calc.) | 5 V only | [repo](https://github.com/bitaxeorg/bitaxeGamma) |
| Bitaxe SupraHex (701 / 702) | 6 × BM1368 | 4.0–4.2 | ~75 | 17.9–18.8 (calc.) | 12 V | [repo](https://github.com/aaron3481/supraHex): not a bitaxeorg repo, so **unverified** |
| Bitaxe Supra (401 / 402 / 403) | 1 × BM1368 | 0.625 at stock | 12 (401) | 19.2 (calc.) | 5 V only | [repo](https://github.com/bitaxeorg/bitaxeSupra) |
| Bitaxe Ultra Hex (302 / 303), **unfinished** | 6 × BM1366 | 2.6–3 | ~50 | ~17–22 (calc.) | 12 V | [repo](https://github.com/bitaxeorg/ultraHex) |
| NerdOCTAXE+ (Patsch91) | 8 × BM1368 | ~5 | ~100 | ~20 (calc.) | 12 V, XT60 | [repo](https://github.com/Patsch91/NerdOCTAXE-Plus) |
| Bitaxe GammaDuo (650) | 2 × BM1370 | 1.63 at stock | 35 | 21.4 (calc.) | 5 V | [wiki](https://osmu.wiki/bitaxe/650) |
| NerdQAxe+ | 4 × BM1368 | ~2.5 | ~55 | ~22 | 12 V | [repo](https://github.com/shufps/qaxe) |
| Bitaxe Ultra (201–207) | 1 × BM1366 | 0.434 at stock | 12 | 27.7 (calc.) | 5 V only | [repo](https://github.com/bitaxeorg/bitaxeUltra) |
| Bitaxe Max (102) | 1 × BM1397 | 0.286 at stock (README: "over 0.4") | 12 | 42.0 (calc.) | 5 V | [repo](https://github.com/bitaxeorg/bitaxeMax) |
| **NerdOCTAXE-γ** | 8 × BM1370 | ~9.5–10.5 older boards; 11.42 at stock on rev 3.x | ~160 older boards; rev 3.x not published | ~15–17 (calc.) | 12 V, XT60 | [repo](https://github.com/Patsch91/NerdOCTAXE-Gamma) |

**Notes:**
- **Boards with no published power.** The NerdQAxe firmware also supports NerdEKO (12 × BM1370), NerdQX, Q1370, Q1373, NerdAxeGaia, NerdAxeGamma and NerdAxe. None of them has a published power figure, so they have no efficiency rating.
- **Firmware-only numbers.** Many Bitaxe "at stock" numbers come from firmware settings, not from a rating, and a few of the firmware's power targets look off.
  The **Gamma's ~1.2 TH/s** comes from the designers' own README.

---

## Notes on the sources

- **Official sources only.** Shops, resellers and spec-aggregator sites were used only as cross-checks, never as a source.
  Where they were checked, their main numbers (hashrate, power, efficiency) broadly agree with the ones above.
  Resellers disagree with each other on some details, such as the S19K Pro's weight. Some also list a 136 TH/s S19K Pro that Bitmain doesn't. None of those numbers are used here.
- **Bitaxe, NerdQAxe++ and NerdOCTAXE-γ** are open-source designs, so their official sources are the designers' GitHub pages and the official firmware.
  GitHub links point to the exact file version that was read.
  The NerdOCTAXE-γ's designer is Patsch91, not bitaxeorg or shufps.
- **Bitmain:** Bitmain's support pages block automated tools, so the same articles were read through the help center's public data feed. The text and article numbers are the same.
  The manual PDF is on Bitmain's own file server.
- **Makers' pages:** many makers' pages block automated tools, so most of them were read with a page-reading service instead. The numbers are still the makers' own.
  Spot checks:
  - The MicroBT M70S+ manual matches the table exactly (244–280 TH/s, 3140–3500 W, 12.5 J/TH).
  - Block's Proto page shows 819 TH/s and 14.1 J/TH.
  - The newer Nano 3S firmware file is really on Canaan's server.
- **Unverified models are left out of every table.** These are models that only resellers list, such as MicroBT M72/M78/M79, a Bitmain "S23 318T" and a NerdQAxe++ "Rev 6.1".
