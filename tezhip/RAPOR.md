# Tezhip kompozisyonları 01–08: üretim ve doğrulama raporu

## 1. Dosyalar

| Dosya | İçerik |
|---|---|
| `palette.json` | İznik esaslı ortak palet ve ekollere göre alt kümeler |
| `motifs.py` | Motif kütüphanesi (geometri çekirdeği, motifler, bordür, girih, helezon dolgu) |
| `compositions.py` | Yedi kompozisyon (`comp01` … `comp07`) |
| `build.py` | SVG → PDF (vektör) ve PNG (600 dpi) üretimi (cairosvg 2.9) |
| `validate.py` | Kenar boşluğu ve simetri ölçümü, `validation.json`, `contact_sheet.png` |
| `motif_test.py` → `motif_test.svg/png` | Motif sözlüğü test sayfası |
| `tezhip_XX.svg / .pdf / .png` | Kaynak, baskı ve raster çıktılar (XX = 01…08) |
| `hat_alanlari.json` | Her görselin boş hat alanının biçimi, ölçüleri ve merkezi |

Yeniden üretmek için: `python3 build.py && python3 validate.py`

Bütün görsellerde ortak teknik özellikler şunlardır:
- **Sayfa:** `width="500mm" height="700mm" viewBox="0 0 500 700"`.
- **Tezhip alanı:** 400 × 600 mm, 50 mm paspartu payıyla sayfaya ortalı.
- **Kırpma:** Bütün içerik tezhip alanına `clipPath` ile kırpılır; alanın dışına hiçbir çizgi, motif veya gölge taşmaz.
- **Raster çıktı:** PNG'ler 11811 × 16535 px, RGB ve 600 dpi pHYs bilgisiyle kaydedildi.

## 1a. Hat (kitâbe) alanları

İkinci revizyonda her kompozisyonun merkezine, hat yazılmak üzere **tamamen boş, astar renkli** bir alan açıldı; kenarında yalnız ince cetvel ve tahrir vardır. Bu alanın içinde hiçbir motif bulunmaz. 08 ise doğrudan bu amaçla, örnek alınan kitap kapağı/levha düzenine göre tasarlandı.

Tablodaki ölçüler mm cinsindendir ve sayfanın sol üst köşesine göre verilmiştir. "Güvenli dikdörtgen", hat alanına kenardan 4 mm boşluk bırakarak sığan en büyük düz dikdörtgendir; satır düzeni planlanırken bu ölçü esas alınabilir.

| # | Alanın biçimi | Dış ölçü (G × Y) | Güvenli dikdörtgen | Merkez (x, y) |
|---|---|---|---|---|
| 01 | dilimli oval (şemse içi) | 142,9 × 241,7 | 100,0 × 151,9 | 250,0 / 350,0 |
| 02 | dilimli oval kartuş | 190,2 × 251,8 | 133,1 × 161,8 | 250,0 / 322,8 |
| 03 | daire | Ø 166,0 | 110,0 × 108,8 | 250,0 / 350,0 |
| 04 | düzgün sekizgen (hâtem içi) | 154,1 × 154,0 | 100,1 × 101,7 | 250,0 / 350,0 |
| 05 | sivri kemerli pano (mihrabiye) | 237,4 × 378,5 | 222,6 × 294,8 | 250,0 / 332,4 |
| 06 | dilimli oval (turunç içi) | 117,3 × 249,0 | 76,2 × 168,7 | 250,0 / 350,0 |
| 07 | daire | Ø 144,0 | 93,6 × 94,0 | 250,0 / 350,0 |
| 08 | daire (halka madalyon içi) | Ø 172,0 | 114,0 × 113,3 | 250,0 / 350,0 |

Kullanım önerisi:
- **Yuvarlak alanlar (03, 07, 08):** celî sülüs veya istif edilmiş besmele/âyet için uygundur.
- **Dikey ovaller (01, 06):** iki-üç satırlık bir kompozisyon için uygundur.
- **Mihrabiye (05):** en geniş alandır; çok satırlı bir metne (hilye, kıta, âyet levhası) elverişlidir.

Hat elle ya da dijital olarak SVG/PDF üzerine eklenebilir. SVG'de alan `fill="#F7F3E8"` dolgulu tek bir yoldur; doğrudan onun üstüne yeni bir katman eklenebilir.

## 2. Motif sözlüğü (`motifs.py`)

Her motif `(A, fill, stroke, sw, …)` parametrelerini alır. Burada `A` afin yerleştirme matrisi, `sw` ise tahrir kalınlığıdır (mm). Noktalar Python tarafında dönüştürüldüğü için tahrir kalınlığı ölçekten bağımsızdır. Organik konturların hepsi kübik Bézier'dir: ya doğrudan `C` komutları kullanılır ya da örnek noktalar Catmull-Rom yöntemiyle Bézier'e çevrilir.

- **Rûmî:**
  - `rumi(kind='tek'|'cift'|'simetrik')`
  - Dış sırt, sivri baş ve iç kenarda tırnak (çentik) ile ikinci uç vardır; ince iç tahrir ("göz") eklenir.
- **Hatâyî grubu:**
  - `penc`: n yapraklı, iki kat taç yapraklı, göbekli.
  - `gonca`: tomurcuk ve çanak yaprakları.
  - `hatayi`: yelpaze biçimli, iki kat taç, kadeh ve göbek.
  - `yaprak`: düz ya da tırtıllı kenarlı, damarlı.
- **Saz yolu:**
  - `saz`: omurga Bézier'i boyunca kalınlık profili verilmiş hançer yaprak.
  - Dış kenarı testere dişli, damar boyunca iki renklidir.
- **Bulut:**
  - `bulut`: iki ucu zıt yönde helezonla kıvrılan, loblu S-şerit (ebrî bulut).
  - Merkeze göre nokta simetriktir (C2).
- **Çintemani:**
  - `cintemani`: üçgen dizilmiş üç benek (iç hilalli) ve altında iki dalgalı "kaplan çizgisi".
- **Şemse ve salbek:** `lobed_ellipse` (dilimli şemse), `semse_finial` (tepelik), `salbek_path`.
- **Köşebent:** `kosebent_path`, iç kenarı dilimli çeyrek oval.
- **Mühr-i Süleyman:**
  - `muhr(n=6|8)`: geçmeli, çift tahrirli şerit.
  - n=6 iki üçgenden kurulan hexagramdır ({6/2}); n=8 iki kareden kurulan sekiz köşeli hâtemdir ({8/2}).
  - Alt-üst sırası `weave()` ile kısıt yayılımına göre kurulur: her şerit boyunca bir üstten, bir alttan geçer.
- **Yıldız-poligon ağı:**
  - `girih('488'|'4612'|'10')` Hankin'in "temas eden poligonlar" yöntemini kullanır. Temel döşemeler:
    - 4.8.8 döşemesi → 8'li ağ
    - 4.6.12 döşemesi → 12'li ağ
    - ongen çevresinde 10 beşgenden oluşan yama → 10'lu rozet
  - Ek olarak `rosette(n)` klasik n kollu rozeti kurar: merkezde yıldız, çevresinde altıgen yaprak halkası.
- **Zencerek ve tığ:**
  - `zencerek`: iç içe badem halkalar ve boncuklardan oluşur; köşelerde dört yapraklı çiçek vardır.
  - `tig_frame` / `tig_path`: içbükey kenarlı, uzun-kısa dönüşümlü, dışa bakan tığlar.
  - `outer_frame` her kompozisyonda ortaktır. Dıştan içe sıra: dış cetvel (tezhip alanının sınırı), tığ kuşağı, zencerek kenar suyu.
- **Dolgu ve bordür:**
  - `scroll_field`: tuğla düzeninde helezonlar; komşu helezonlar S-kıvrımla bağlanır.
  - `band_scroll`: koşan dal; yarım dalga sayısı tektir, böylece kenar ortasına göre aynalı olur.
  - `frame_band`: üst ve sol kenar kurulur, alt ve sağ kenar aynalanır.
  - `sym_band_items`: aynalı birim dizisi.

## 3. Ölçümler

### 3.1 Kenar boşlukları

Ölçüm yöntemi: astar rengi #F7F3E8'den herhangi bir kanalda 8 seviyeden fazla sapan ilk ve son piksel bulunur. 1 mm = 23,622 px.

| # | sol px | sağ px | üst px | alt px | sol/sağ mm | üst/alt mm | yatay fark | dikey fark |
|---|---|---|---|---|---|---|---|---|
| 01 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 02 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 03 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 04 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 05 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 06 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 07 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |
| 08 | 1181 | 1181 | 1180 | 1180 | 50,00 | 49,95 | 0 | 0 |

Teorik değer 50 mm × 23,622 = 1181,1 px'tir. Üst ve alt kenarda ölçülen 1180 px, aşağıda açıklanan 0,22 px'lik raster faz kaydırmasından gelir: ilk satır kısmen kaplanır. Bütün görsellerde fark 0 px'tir; ±1 px ölçütü karşılanır.

### 3.2 Ayna simetrisi

Ölçüm yöntemi: PNG dizisi aynalanır ve orijinalle karşılaştırılır. Herhangi bir kanalda 64 seviyeden fazla fark gösteren pikseller sayılır. Ayrıca ortalama mutlak fark (0–255 ölçeğinde) verilir.

| # | Simetri | Dikey eksen (sol↔sağ) | Yatay eksen (üst↔alt) | Sonuç |
|---|---|---|---|---|
| 01 | D2 | %0,0513 (OMF 0,13) | %0,0332 | geçti |
| 02 | dikey ayna | %0,0000 | — | geçti |
| 03 | D2 + D12 halka | %0,0356 | %0,0217 | geçti |
| 04 | D2 + D4 merkez | %0,0368 | %0,0368 | geçti |
| 05 | dikey ayna | %0,0001 | — | geçti |
| 06 | D2 | %0,0000 | %0,0001 | geçti |
| 07 | D2 + D8 halka | %0,0613 | %0,0538 | geçti |
| 08 | D2 (D4 halka) | %0,0476 | %0,2280 | geçti |

Değerler hat alanlı ikinci revizyona aittir. 08'in yatay eksendeki görece yüksek değeri, halka üzerindeki geçmeli {8/3} yıldız madalyonlarından gelir (§3.4).

Bütün değerler %0,5 eşiğinin altındadır. Ayrıntılı ham sonuçlar `validation.json` dosyasındadır.

### 3.3 Doğrulama sürecinde düzeltilenler

İlk ölçümde 01, %0,53 ve %1,34 sapmayla eşiği geçemedi. Fark haritası çıkarılarak kaynaklar bulundu ve yapısal olarak giderildi:

1. **Raster fazı.**
   - 600 dpi'da sayfa 11811,02 × 16535,43 px eder; tam sayıya yuvarlanan PNG'de 350 mm ekseni 8267,72 px'e düşer, dizinin aynalandığı eksen ise 8267,5 px'tir.
   - Bu yüzden aynalanan görüntü 0,44 px kayıyordu.
   - Çözüm: yalnız PNG üretiminde tezhip alanı 9,2 µm (0,22 px) kaydırıldı (`build.py: raster_phase`). Böylece geometrik eksen piksel ızgarasının orta çizgisiyle çakışır.
   - SVG ve PDF değişmedi. Kayma baskı toleransının çok altındadır.
2. **Tığ sayısının tek çıkması:** uzun-kısa dönüşüm aynada kayıyordu. Her kenarda tığ sayısı çifte zorlandı.
3. **Şemse tığları:** örnekleme artık simetri ekseninin konturu kestiği noktadan, tam ara değerle başlıyor.
4. **Zencerek halkaları:** halkaların üst üste binme sırası aynada tersine dönüyordu. Önce bütün koyu kenarlar, sonra altın iç çizgiler çiziliyor; zincir düz birleşiyor.
5. **Köşe pençleri ve 01'in salbekleri:** beş yapraklı pençin yatay aynası yoktur. Köşeler ve salbekler tek kopya olarak kurulup aynalanıyor.
6. **Eksen dikişi:** yarım ve çeyrek klipler eksenin 0,05 mm ötesine taşırıldı; böylece kenar yumuşatma (antialias) kaynaklı ince "dikiş" çizgisi oluşmuyor.

### 3.4 Kalan sapmanın kaynağı

Kalan sapma (%0,04–0,07) büyük ölçüde geçmeli (alttan-üstten) şeritlerden gelir: 04 ve 07'deki Mühr-i Süleyman ile 04'ün köşe hâtemleri. Bu bir hata değil, matematiksel bir zorunluluktur. Almaşık geçme yansıma altında korunmaz, çünkü yansıma bir kesişimde hangi şeridin üstte kaldığını değiştirmez ama dönüşümün sırasını tersine çevirir. Bu yüzden geçmeli bir şekil yalnız dönme simetrisine sahiptir; ayna simetrisi ancak alt-üst değişimiyle birlikte (antisimetri) geçerlidir.

Bu nedenle şu tercihler yapıldı:
- **04'ün lacería ağı:** düz, birleşik şerit (zellige şeridi) olarak çizildi ve tam aynalıdır.
- **Merkezdeki hâtemler:** gerçek almaşık geçme olarak bırakıldı.

## 4. Kompozisyonlar: ekol ve şema özeti

İkinci revizyonda yapılan değişiklikler:
- **01:** Şemse büyütüldü (90 × 138 mm yarı eksen) ve içi boş bırakıldı; dolgu şemsenin kuşağında kaldı.
- **02:** Ağacın önüne kobalt kuşaklı dilimli kartuş kondu; dallar ve saz yaprakları kartuşun arkasından dolaşır.
- **03:** Merkez rozet kaldırıldı; yerine üzerinde 12 küçük rozet bulunan lacivert bir halka geldi (D12 korunur).
- **04:** Sekiz köşeli hâtemin iki karesinin kesişiminden doğan sekizgen boş bırakıldı.
- **05:** Kemer içinde iç içe ikinci bir kemer açıldı; kandil kaldırıldı.
- **06:** Mercan iç şemse yerine boş, dilimli bir oval geldi.
- **07:** Merkezdeki hexagram, madalyonun üst ve alt eksenine iki küçük geçmeli madalyon olarak taşındı.

Aşağıdaki tanımlar ilk sürümü anlatır; merkez öğeler yukarıdaki değişikliklerle birlikte okunmalıdır.


**01 — Osmanlı klasik (16. yy).**
- **Merkez:** 22 dilimli lacivert şemse; altın sırt, tahrir ve çevresinde tığlar vardır. Dikey uçlarda tepelikli iki salbek bulunur.
- **Köşeler:** dört köşebent.
- **Dolgu:** Şemse ve köşebentlerde lacivert üzerine altın ve firuze hatâyî-penç-gonca helezonları, rûmî yapraklar.
- **Zemin:** Astar zemin, ince altın halkâr helezonlarla doludur.
- **Bordür:** lacivert zemin üzerinde altın koşan dal ve hatâyî-penç.
- **Palet ve simetri:** lacivert, altın, firuze; D2.

**02 — Osmanlı saz yolu ve çintemani.**
- **Şema:** Astar zemin üzerinde, tabandaki kobalt vazodan yükselen ağaç kompozisyonu.
- **Unsurlar:** kıvrık, tırtıllı, iki renkli saz yaprakları; büyük mercan-kobalt hatâyîler; penç ve goncalar.
- **Kenar suyu:** çintemani dizisi (mercan benek, kobalt dalga).
- **Palet ve simetri:** tam İznik paleti, mercan belirgin; yalnız dikey ayna.

**03 — Memlük (14. yy Kahire mushaf tezhibi).**
- **Zemin:** altın zemin üzerinde 4.6.12 döşemesinden Hankin yöntemiyle (θ = 60°) üretilmiş 12'li yıldız ağı. Lacivert yıldızların her birinde altın 12'li mini rozet vardır; firuze kare yıldızlar seyrek bir aksan oluşturur.
- **Merkez:** dilimli ve tığlı çerçeve içinde iki katlı, D12 simetrili 12 kollu rozet.
- **Bordür:** 8'li girih şeridi.
- **Palet ve simetri:** lacivert, altın, az firuze; D2 bütün, D12 rozet.

**04 — Nasrî / Endülüs (Elhamra etkisi).**
- **Zemin:** 4.8.8 döşemesinden (θ = 67,5°) üretilmiş lacería. Astar şeritlerin arasındaki sekizgen yıldızlar kobalt ve zümrüt olarak satranç düzeninde boyanmış, kare yıldızlar mercan, ara zemin altındır (zellige etkisi).
- **Merkez:**
  - **Çerçeve:** zümrüt kare çerçeve (D4), mercan çeyrek rozetli.
  - **Çerçeve içi:** daha ince ölçekli zellige ağı.
  - **Merkezi motif:** kobalt sekiz kollu yıldız üzerinde geçmeli sekiz köşeli hâtem; ortada 8'li rozet.
- **Bordür:** karo dizisi.
- **Palet:** kobalt, zümrüt, altın, mercan.

**05 — Timurlu, Herat ekolü (15. yy).**
- **Ana çerçeve:** Lacivert zeminde sivri kemerli mihrabiye.
- **Kemer içi:** çok ince ölçekli (helezon aralığı 15 mm) altın-firuze hatâyî dolgu ile altın ve firuze Çin bulutları.
- **Kemer üstü:** kemer tepesinden sarkan zincirli kandil-şemse.
- **Köşelikler:** altın zemin üzerinde lacivert ince helezon.
- **Alt kartuş:** bulut şeridi.
- **Palet ve simetri:** beyaz yalnız çiçek göbeklerinde ve küçük ayrıntılarda kullanıldı; dikey ayna.

**06 — Safevî (16. yy Tebriz/Kazvin cilt ve tezhibi).**
- **Zemin:** altın zemin, yalnız çok hafif bir varak parlaklık gradyanıyla. Lacivert, mercan, firuze ve zümrüt hatâyî ile doludur.
- **Merkez:**
  - **Şemse (turunç):** uzun, 30 dilimli lacivert şemse; uçlarında tepelik ve çift salbek bulunur.
  - **Şemse dolgusu:** şemsenin içi altın dolgulu.
  - **İç şemse:** mercan zeminli.
- **Köşeler:** dairesel köşebentler.
- **Bordür:** lacivert üzerinde altın kartuş ile firuze madalyon dizisi.
- **Kısıtlar ve simetri:** Çin bulutu ve hayvan figürü kullanılmadı; D2.

**07 — Sentez.**
- **Zemin:** Memlük 8'li girih ağı (lacivert, kobalt, firuze, altın).
- **Merkez:** büyük tığlı madalyon:
  - D8 simetrili 8 kollu rozet halkası.
  - Halkanın aralarında Safevî bulutları.
  - Merkezde astar zemin üzerinde geçmeli altın Mühr-i Süleyman (hexagram) ve Osmanlı hatâyî-gonca dolgu.
- **Köşebentler:** Osmanlı hatâyî.
- **Bordür:** Safevî bulut ve penç.
- **Palet:** tam palet.

**08 — Boş merkezli halka madalyonlu kitap kapağı / levha (klasik Osmanlı üslûbu).**
Tasarım, kullanıcının örnek gösterdiği düzene göre yapıldı.
- **Merkez:** kobalt halka madalyon; içinde hatâyî-rûmî helezonları vardır. Halkanın dört ekseninde geçmeli {8/3} yıldız madalyonları, dışında ise dilimli çıkıntılar bulunur: dikey eksende uzun, yatayda kısa, uçlarında tığ vardır. Çaprazlarda firuze dilimli madalyonlar yer alır.
- **Köşebentler:** dört adet, tığlı.
- **Zemin:** Astar zemin açık bırakıldı; üstünde yalnız zincirli sarkan salbekler (ince altın tel, boncuk, lacivert badem damla, uçta tığ) vardır.
- **Bordür:** kobalt koşan dal; kenar ortalarında ve köşelerde firuze dilimli madalyonlar.
- **Simetri:** D2; halka D4.

## 5. Bilimsel notlar ve bilinçli tercihler

1. **Mühr-i Süleyman ile D4/D8 talebinin çelişmesi.** Osmanlı terminolojisindeki altı köşeli hexagramın simetri grubu D6'dır. Bu grup ne D4'ü ne de D8'i içerir: ortak eksenlerle D6 ∩ D8 = D2 ve D6 ∩ D4 = D2'dir.
   - **04 (Nasrî):** Mağrib-Endülüs kullanımında *hâtem-i Süleymân* adı sekiz köşeli, iki kareden oluşan yıldıza da verilir. Bu yüzden 04'te {8/2} hâtem kullanıldı. Bu motifin grubu D8 ⊃ D4'tür; kare çerçeveyle birlikte merkez grubu tam D4 olur.
   - **07 (Sentez):** Osmanlı tanımına sadık kalınarak hexagram kullanıldı. Rozet halkası D8'dir; merkezdeki motifin kendisi D6'dır. Bu nedenle bileşik merkez grubu kesin anlamda D2 olur.
2. **Geçme ve ayna simetrisi.** Bkz. §3.4. Almaşık geçme ancak dönme simetrisini korur; ayna simetrisi alt-üst değişimiyle birlikte (antisimetri) geçerlidir. Ayna simetrisi istenen geniş ağlarda düz şerit tercih edildi.
3. **Gradyan.** Gradyan yalnız 06'nın altın zemininde, çok hafif radyal bir "varak parlaklığı" olarak kullanıldı (#D2AC33 → #C9A227); geri kalan her şey düz dolgudur.
4. **Mercan kırmızısının kabartı hissi.** Bu his gölge veya gradyanla değil, tahrir kalınlığı ve beneklerdeki koyu kontur ağırlığıyla verildi. Çini sırrının düz dolgusu korunmuş oldu.
5. **Yazı yasağı.** Hiçbir görselde yazı, hat, harf veya rakam yoktur.
6. **Yöntemin sınırı.** Motifler sözlüğün tarihî tiplerini parametrik olarak yeniden kurar; belirli bir eserin kopyası değildir. Ekol nitelemeleri kompozisyon şeması, palet ve motif repertuvarı düzeyindedir.
