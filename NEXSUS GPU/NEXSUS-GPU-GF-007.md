# NEXSUS GPU Group Fabric — Alıcı İçi Kuyrukların İşlevsel Simülasyon Modeli

**Doküman Kodu:** `NEXSUS-GPU-GF-007`  
**Konu:** 8 Line'lı Group için alıcı kuyruğu, öncelikli gönderim, akış kontrolü ve bağımsız ilerleme simülasyonu  
**Statü:** İşlevsel simülasyon taslağı  
**Bağlantılı Belgeler:** `NEXSUS-GPU-GF-002` – `NEXSUS-GPU-GF-006`

---

## 1. Amaç

Bu belgenin amacı, NEXSUS GPU Group Fabric mimarisinin temel davranışlarını fiziksel donanım ayrıntılarından bağımsız biçimde test edebilecek bir işlevsel model tanımlamaktır.

Simülasyonun ilk sürümü aşağıdaki sorulara cevap vermelidir:

- Alıcı kuyruğu FIFO sırasını doğru koruyor mu?
- Gönderici, öncelikli işleri doğru sırada kuyruğa yerleştirebiliyor mu?
- Dolu bir kuyruk, yalnızca ilgili aktarımı mı durduruyor?
- Birden fazla alıcı aynı anda çalışabiliyor mu?
- Kuyrukta yer açıldığında bekleyen aktarım yeniden başlayabiliyor mu?
- Bağımlılık, kaynak çakışması veya karşılıklı bekleme durumları doğru yönetiliyor mu?

Bu aşamada amaç, fiziksel hız ölçmek değil, mimari kuralların doğruluğunu sınamaktır.

## 2. Simülasyonun Temel Yapısı

İlk model bir Group ve sekiz Line içerir.

```text
NEXSUS GPU Group
│
├── Sub-group A
│   ├── Line 0 ──┐
│   ├── Line 1 ──┤
│   ├── Line 2 ──┤── FP64 Engine A
│   └── Line 3 ──┘── Matrix Engine A
│
├── Sub-group B
│   ├── Line 4 ──┐
│   ├── Line 5 ──┤
│   ├── Line 6 ──┤── FP64 Engine B
│   └── Line 7 ──┘── Matrix Engine B
│
├── Group Fabric
├── Group PRAM
└── Alıcı birimlerin yerel kuyrukları
```

Her alt grubun FP64 ve Matrix Engine kaynakları kendisine aittir. Diğer alt grubun motorlarıyla kaynak paylaşımı yapılmaz.

Group PRAM erişimleri Group Fabric üzerinden yürütülür. Line PRAM ise ilgili Line'ın yerel belleği olarak kalır.

## 3. Alıcı Kuyruğu Modeli

Her alıcı için ayrı bir yerel kuyruk tanımlanır.

Başlangıçta iki kapasite seçeneği test edilir:

| Parametre | Değer |
|---|---:|
| Küçük kuyruk | 4 kayıt |
| Büyük kuyruk | 8 kayıt |
| Okuma düzeni | FIFO |
| Öncelik kararı | Gönderici tarafı |
| Dolu kuyruk davranışı | Aktarımı bekletme |
| Boş kuyruk davranışı | Okuma yapmama |

Bu kapasiteler karşılaştırma amaçlıdır. Simülasyon sonuçları hangi kapasitenin daha uygun olduğunu gösterebilir; fiziksel devre alanını veya en iyi kapasiteyi tek başına kanıtlamaz.

Her kuyruk aşağıdaki bilgileri tutar:

- Kapasite.
- Mevcut kayıt sayısı.
- Okuma konumu.
- Yazma konumu.
- FIFO sırasındaki kayıtlar.
- Doluluk ve kullanılabilir alan durumu.

Kuyruk doluyken yeni kayıt kabul edilmez. Kayıt kaybı olmamalıdır.

## 4. İş Kaydı

Simülasyonda her iş, en azından aşağıdaki mantıksal alanlarla temsil edilir:

```text
WorkItem
├── work_id
├── source_id
├── destination_id
├── operation_type
├── priority
├── dependency_id
├── data_reference
└── status
```

`priority`, göndericinin sıralama kararında kullanılır. Alıcı kuyruğu bu alanı değerlendirmek zorunda değildir.

`dependency_id`, bir işin başka bir işin sonucunu bekleyip beklemediğini test etmeye yarar. Bağımlılık yoksa alan boş olabilir.

`data_reference`, büyük verinin kendisini kuyrukta kopyalamak yerine ilgili veri veya PRAM adresine işaret edebilir. Bu, ilk modelde tercih edilen yaklaşımdır; gerçek kayıt biçimi henüz belirlenmemiştir.

## 5. Gönderici Tarafındaki Sıralama

Gönderici, gönderilmeye hazır işleri önceliklerine göre sıralar.

Örnek:

| İş | Öncelik | Hedef |
|---|---:|---|
| İş A | 2 | FP64 Engine A |
| İş B | 1 | Matrix Engine A |
| İş C | 3 | FP64 Engine A |
| İş D | 1 | FP64 Engine A |

Bu tabloda `1` en yüksek önceliği temsil eder.

Her hedef için uygun gönderim sırası belirlenir. Aynı hedefe yönelen İş A, C ve D arasında öncelik uygulanır. Matrix Engine A'ya giden İş B, FP64 Engine A'nın kuyruğundaki sıralamaya bağlı değildir.

Eşit öncelikli işler için geliş sırası korunur. Böylece aynı öncelik sınıfındaki işler arasında gereksiz sıralama değişikliği yapılmaz.

Öncelik yalnızca gönderime hazır işler arasında değerlendirilir. Bir işin bağımlılığı henüz karşılanmamışsa, yüksek öncelikli olması tek başına işlenebilir olduğu anlamına gelmez.

## 6. Alıcı Tarafındaki İşleyiş

Alıcı, kuyruğundan yalnızca sıradaki kaydı okur.

```text
1. Kuyruk boş mu?
   ├── Evet: Bekle.
   └── Hayır: Devam et.

2. Sıradaki kaydı al.

3. Kaydın çalıştırılabilir olduğunu doğrula.

4. İşlemi yürüt veya ilgili kaynağa teslim et.

5. Kayıt tüketildiğinde kuyruğun yerini boşalt.

6. Sonraki kayıt için aynı döngüyü sürdür.
```

Bağımlılık kontrolü, mümkün olduğunca gönderim öncesinde veya işi yürütmeye yetkili kontrol katmanında yapılmalıdır. Alıcı kuyruğunun başındaki bir kayıt çalıştırılamıyorsa, aynı kuyruktaki sonraki kaydı atlayıp atlayamayacağı ayrıca tanımlanmalıdır.

İlk modelde **FIFO sırası korunur ve kuyruk başındaki kayıt atlanmaz**. Böylece temel davranış kolayca doğrulanır. Bu kuralın ileride performans darboğazı oluşturup oluşturmadığı ayrı bir test konusu olacaktır.

## 7. Simülasyon Zamanı ve Olaylar

Simülasyon, mantıksal adımlarla ilerler. İlk sürümde her adım fiziksel olarak bir saat çevrimine eşit kabul edilmek zorunda değildir.

Her adımda şu olaylar değerlendirilir:

1. Tamamlanmış işlemler ve serbest kalan kaynaklar güncellenir.
2. Bağımlılıkları karşılanan işler gönderime hazır hâle gelir.
3. Göndericiler hedef ve öncelik sırasını belirler.
4. Kuyruk kapasitesi uygunsa kayıt kabul edilir.
5. Hazır alıcılar kendi FIFO kuyruklarından kayıt tüketir.
6. Dolu kuyruklar ve bekleyen aktarım talepleri güncellenir.
7. İlerleme, bekleme, kaynak kullanımı ve hata sayaçları kaydedilir.

Aynı simülasyon adımında okuma ve yazmanın birlikte gerçekleşmesine izin verilip verilmeyeceği açık bir parametre olmalıdır. İlk karşılaştırmada hem aynı adımda boşalan yere yazma hem de sonraki adıma kadar bekleme davranışları test edilebilir.

## 8. Temel Test Senaryoları

### GF-TEST-001 — FIFO doğrulaması

Bir alıcı kuyruğuna A, B ve C kayıtları bu sırayla yerleştirilir.

**Beklenen sonuç:** Alıcı A, B ve C kayıtlarını aynı sırayla tüketir.

### GF-TEST-002 — Öncelik sıralaması

Aynı hedefe gidecek farklı önceliklerdeki işler gönderici tarafında bekletilir.

**Beklenen sonuç:** Kuyruğa kabul edilen kayıtların sırası, gönderici sıralamasını yansıtır. Alıcı ayrıca öncelik hesabı yapmaz.

### GF-TEST-003 — Dört kayıtlık kuyruğun dolması

Kuyruk kapasitesi 4 olarak ayarlanır ve alıcı kayıt tüketmeden dört kayıt gönderilir.

**Beklenen sonuç:** İlk dört kayıt kabul edilir. Beşinci kayıt kuyruğa yazılmaz; aktarım bekletilir. Alıcı bir kayıt tükettiğinde bekleyen aktarım yeniden denenebilir.

### GF-TEST-004 — Sekiz kayıtlık kuyruk karşılaştırması

GF-TEST-003, kapasite 8 ile tekrarlanır.

**Beklenen sonuç:** Aynı trafik altında sekiz kayda kadar bekleme kabul edilir. İki modelin bekleyen aktarım sayıları ve kuyruk dolulukları karşılaştırılır.

### GF-TEST-005 — Bağımsız alıcılar

FP64 Engine A'nın kuyruğu doldurulur. Aynı anda Matrix Engine A'ya bağımsız işler gönderilir.

**Beklenen sonuç:** FP64 Engine A'ya yönelik yeni aktarım beklerken Matrix Engine A çalışmaya devam eder.

### GF-TEST-006 — Alt grupların bağımsızlığı

Sub-group A'da yoğun trafik oluşturulur. Sub-group B'ye bağımsız işler gönderilir.

**Beklenen sonuç:** Sub-group B, yalnızca Sub-group A yoğun olduğu için durmaz. Ortak bir kaynak veya bağlantı çakışması varsa bu ayrı bir bekleme nedeni olarak raporlanır.

### GF-TEST-007 — Çoklu gönderici

Birden fazla Line aynı alıcıya iş göndermek ister.

**Beklenen sonuç:** Gönderim arbitrajı belirli ve tekrarlanabilir bir sıra oluşturur. Öncelik eşitse geliş sırası korunur. Aynı kayıt iki kez kabul edilmez.

### GF-TEST-008 — Geri basınç

Alıcı kuyruğu doldurulur ve gönderim talepleri devam eder.

**Beklenen sonuç:** Kapasiteyi aşan kayıtlar kaybolmaz veya sessizce üzerine yazılmaz. Göndericiler bekleme durumuna geçer; yer açıldığında aktarım devam eder.

### GF-TEST-009 — Bağımlılık kontrolü

İş B, İş A'nın sonucunu gerektirir; ancak İş A henüz tamamlanmamıştır.

**Beklenen sonuç:** İş B, önceliği yüksek olsa bile gerekli veri hazır olmadan yürütülmez.

### GF-TEST-010 — Deadlock ve aç kalma

Birden fazla kaynak arasında karşılıklı bekleme oluşturulur. Ayrı bir testte sürekli yüksek öncelikli işler gönderilir.

**Beklenen sonuç:** Simülatör ilerlemenin durduğu veya düşük öncelikli bir işin aşırı uzun süre beklediği durumları tespit eder. Sorunun otomatik olarak çözüldüğü varsayılmaz.

## 9. Ölçülecek Sonuçlar

Her test için aşağıdaki metrikler kaydedilir:

- Toplam kabul edilen iş sayısı.
- Tamamlanan iş sayısı.
- Kuyruk başına maksimum doluluk.
- Kuyruk başına ortalama doluluk.
- Kuyrukta bekleme süresi.
- Gönderici tarafındaki bekleme süresi.
- Kuyruk doluluğu nedeniyle ertelenen aktarım sayısı.
- Kaynakların meşgul ve boşta kaldığı adım sayısı.
- Bağımsız işlerin gereksiz yere durdurulma sayısı.
- Deadlock veya aç kalma tespitleri.
- Kayıp veya yinelenen kayıt sayısı.

İlk sürümde bu ölçümler mimari doğruluğu ve kuyruk kapasitesi karşılaştırmasını destekler. Fiziksel gecikme, frekans, alan ve güç değerleri için ayrıca donanım modeli gerekir.

## 10. Başarı Koşulları

İlk işlevsel model aşağıdaki koşulları sağlamalıdır:

- FIFO sırası ihlal edilmemeli.
- Kuyruk kapasitesi aşılmamalı.
- Kayıt kaybı veya yinelenmesi olmamalı.
- Öncelik sıralaması gönderici tarafında uygulanmalı.
- Bağımsız alıcılar mümkün olduğunda eşzamanlı ilerlemeli.
- Bağımlılıklar karşılanmadan işlem yürütülmemeli.
- Dolu kuyruk, kapasite açıldığında yeniden veri kabul edebilmeli.
- Beklemenin nedeni ölçülebilmeli ve raporlanabilmeli.

## 11. İkinci Aşama

İlk testler tamamlandıktan sonra şu geliştirmeler değerlendirilebilir:

1. 4 ve 8 kayıtlık kuyrukların karşılaştırılması.
2. Farklı trafik yoğunlukları ve öncelik dağılımları.
3. Group PRAM bankalarına aynı anda gelen erişimlerin modellenmesi.
4. Birden fazla bağımsız çift yönlü kanalın eklenmesi.
5. Kuyruklar arasında kaynak bağımlılıklarının analizi.
6. Gerekirse kredi tabanlı akış kontrolünün eklenmesi.
7. Mantıksal adımların gerçek saat çevrimlerine dönüştürülmesi.

Bu aşamaya kadar fiziksel kanal genişliği, bellek gecikmesi veya çalışma frekansı hakkında varsayımsal performans iddiası oluşturulmayacaktır.

---

## Sonuç

`NEXSUS-GPU-GF-007`, Group Fabric'in alıcı merkezli kuyruklama yaklaşımını test edilebilir bir işlevsel modele dönüştürür.

İlk hedef, 8 Line'lı Group içinde küçük alıcı kuyrukları, gönderici tarafında öncelik sıralaması, FIFO tüketimi ve bağımsız kaynak ilerlemesinin doğru çalıştığını doğrulamaktır.

Bu doğrulama tamamlandıktan sonra fiziksel bağlantı topolojisi ve zamanlama parametreleri daha güvenilir biçimde ele alınabilir.