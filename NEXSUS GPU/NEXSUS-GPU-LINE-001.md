
# NEXSUS GPU — Line Mimarisi

Doküman Kodu: NEXSUS-GPU-LINE-001 · Sürüm: 0.2 · Statü: Kavramsal tasarım

## 1. Line'ın görev tanımı

Line, NEXSUS GPU'nun en küçük bağımsız komut yürütme birimidir. Kendi komut kontrolüne, register erişimine ve işlem kaynaklarına sahiptir. Bir Line tek başına çalışabilir veya aynı Group içindeki diğer Line'larla ortak bir görev yürütebilir.

Tasarımın amacı her Line'a mümkün olan bütün işlem birimlerini koymak değil; ortak kaynakları kullanarak alan tüketimini azaltmak, gerekli durumlarda bağımsız işlem kapasitesi sağlayarak beklemeyi önlemektir.

## 2. Line blok diyagramı

Komut Kontrol Birimi

Fetch · Decode · Komut durumu

Operand Erişim Birimi

Register · Page RAM · Operand hazırlama

Ortak İşlem Kaynağı

Tamsayı / mantık

Paylaşılan aritmetik alt devreler

Kayan Nokta Birimi

FP32 / FP64

Gerektiğinde ayrı yürütme yolu

İşlem kaynakları, komut türüne göre seçilir. Her iki yolun da her Line'da tamamen bağımsız olması zorunlu değildir.

Sonuç ve Yazma Birimi

Register'a, Page RAM'e veya bellek erişim yoluna sonuç aktarımı

Bu şema işlevsel bölümleri gösterir; henüz kesin transistör düzeyinde devre veya fiziksel yerleşim değildir.

## 3. ALU: kısmen ortak, gerektiğinde ayrı

Line'ın işlem kaynakları üç mantıksal bölümde ele alınır.

- Ortak tamsayı ve mantık yolu: toplama, çıkarma, bit işlemleri, karşılaştırma, kaydırma ve adres hesaplama.
- Kayan nokta yolu: FP32 ve FP64 toplama, çarpma ve çarp-topla gibi işlemler.
- Paylaşılan yardımcı devreler: operand yönlendirme, bazı karşılaştırma ve dönüşüm işlemleri gibi uygun işlevler.

Burada önemli bir ayrım var: Mantıksal olarak ortak tasarım, bütün işlemlerin aynı fiziksel devreyi kullanması demek değildir. Örneğin FP32 ve FP64 aynı kontrol ve bazı aritmetik alt devreleri paylaşabilir; fakat FP64 işlemleri daha geniş veri yolları ve farklı kaynaklar gerektirir.

Ayrıca tamsayı ve kayan nokta komutları ayrı işlem yollarına yönlendirilebilse bile, seçtiğimiz tek komut yürütme modeli nedeniyle bir Line aynı anda iki ayrı komutu başlatmayacaktır. Bağımsız yolların bulunması, tek komutun kaynak kullanımını esnekleştirir; aynı Line'da çift komut yürütme anlamına gelmez.

Bu yaklaşım, farklı işlem yollarının bazı durumlarda eşzamanlı çalışabildiği modern GPU tasarımlarından ayrışan, daha kontrollü bir başlangıç modelidir. NVIDIA'nın Turing mimarisi gibi örneklerde tamsayı ve kayan nokta yollarının ayrılması, karma iş yüklerinde kullanım verimini artırmayı hedefler.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.nvidia.com\&sz=32)

NVIDIA

+1



## 4. Komut yürütme modeli

Her Line bir seferde bir komut yürütür. Bununla birlikte komutlar birden fazla aşamadan geçebilir; bir komut sonuçlanırken sonraki komutun getirilmesi veya çözülmesi, ayrı bir yürütme komutu başlatmakla aynı şey değildir.

| Aşama        | Sorumluluk                                   |
| ------------ | -------------------------------------------- |
| 1. Fetch     | P0 kod sayfasından komutu alma               |
| 2. Decode    | İşlem türünü, kaynakları ve hedefi belirleme |
| 3. Operand   | Register veya Page RAM verisini hazırlama    |
| 4. Execute   | İlgili işlem biriminde komutu yürütme        |
| 5. Writeback | Sonucu hedef register'a veya belleğe aktarma |

Bu beş aşama başlangıç için mantıksal modeldir; kesin saat çevrimi sayısı henüz belirlenmemiştir. Özellikle FP64 işlemleri, Page RAM gecikmeleri ve bellek erişimleri farklı sürelerde tamamlanabilir.

### Örnek komutlar

```
ADD RA, RB, RC
```

RB ve RC değerlerini toplar, sonucu RA'ya yazar.

```
ADD RA, RB, PR[P1:0x00A0]
```

RB ile P1 sayfasının `0x00A0` adresindeki değeri toplar ve sonucu RA'ya yazar. Yazılımın ayrıca bir `LOAD` komutu vermesi zorunlu değildir; ancak Page RAM erişimi gecikirse Line bekleyebilir.

```
FADD32 RA, RB, RC
FADD64 RA, RB, RC
```

Sırasıyla 32 bit ve 64 bit kayan nokta toplama işlemlerini temsil eden örnek komutlardır. Bunlar şimdilik açıklayıcı komut adlarıdır; kesin komut kodlaması daha sonra belirlenecek.

## 5. Register ve Page RAM ilişkisi

Line'ın kendi yerel register havuzu bulunur. Register sayısı ve port sayısı henüz sabitlenmemeli; bunlar komut formatı, operand sayısı ve aynı anda ihtiyaç duyulan erişimler belirlendikten sonra hesaplanmalıdır.

Register havuzu

Sık kullanılan operandlar, geçici değerler ve hızlı sonuçlar. Line'ın birincil çalışma alanı.

Page RAM

Doğrudan adreslenebilir değişkenler, ara sonuçlar ve daha geniş çalışma verisi. Group'lar arası paylaşım için ayrılmış bir alan da tanımlanabilir.

L1/L2 önbellekleri

Bellek erişimini hızlandırır. Page RAM'in yerine geçmez ve açıkça adreslenen çalışma belleğiyle aynı işlevi taşımaz.

Page RAM'in fiziksel olarak her Line'a özel olup olmayacağı veya Group içinde paylaşılacağı ayrı bir bellek yerleşimi kararıdır. Önceki mimari kararımızla uyumlu olarak, register havuzları yerel kalırken Group'lar arası ortak çalışma alanı GPU içindeki ayrılmış Page RAM bölümüyle sağlanabilir.

## 6. FP32 ve FP64 desteği

| Özellik           | FP32                        | FP64                                        |
| ----------------- | --------------------------- | ------------------------------------------- |
| Veri genişliği    | 32 bit                      | 64 bit                                      |
| Tipik kullanım    | Grafik, genel hesaplama     | Daha yüksek hassasiyet isteyen hesaplamalar |
| Donanım yaklaşımı | Ortak kayan nokta altyapısı | Paylaşılan veya özel genişletilmiş yol      |
| Kesin işlem hızı  | Tasarım aşamasında          | Tasarım aşamasında                          |

FP64 desteğinin bulunması, FP32 ile aynı hızda çalışacağı anlamına gelmez. İlk tasarımda FP64 için her Line'a tamamen bağımsız ve yüksek verimli bir birim koymak zorunda değiliz. Bunun alan, güç ve performans maliyetleri simülasyon veya sentez aşamasında değerlendirilmelidir.

## 7. Bekleme ve kaynak yönetimi

Line'ın kontrol birimi en azından şu durumları ayırt edebilmelidir:

- Komut yürütmeye hazır.
- Operand bekliyor.
- İşlem birimi meşgul.
- Sonuç yazımı bekleniyor.
- Bellek erişimi bekleniyor.
- Hata veya geçersiz komut durumu.

Line, kendi içindeki sıradan işlemler için her seferinde Global Group Manager'a başvurmamalıdır. Yerel yürütme yerel kontrol altında kalır; Group Manager, kaynak tahsisi ve Group içi koordinasyonu yürütür. Global yöneticiler ise çoklu Group görevleri ve ortak kaynakların yönetimiyle ilgilenir.

Bir Line bellek yüzünden beklediğinde, Group içindeki diğer Line'lar bağımsız işleri sürdürebilir. Bunun mümkün olması için bağımlılıkların ve kaynak çakışmalarının doğru izlenmesi gerekir; yalnızca bir bekleme durumu bayrağı koymak yeterli değildir.

## 8. Henüz sabitlenmeyen tasarım kararları

Line'ın ana mimarisi artık belirginleşti. Aşağıdaki ayrıntılar ise ölçüm veya komut kümesi tasarımı olmadan kesinleştirilmemeli:

1. Register sayısı, genişliği ve okuma/yazma portları.
2. ALU ve FPU işlem gecikmeleri ile işlem başlatma aralıkları.
3. FP64 yolunun her Line'da mı, yoksa belirli Line yapılandırmalarında mı bulunacağı.
4. Page RAM erişim protokolü ve bellek beklemelerini azaltma yöntemi.
5. Hata algılama, komut iptali ve sonuçların güvenli biçimde yazılması.

Tasarım kararı: NEXSUS GPU Line; tek komut yürütmeli, FP32/FP64 destekli, kısmen ortak işlem kaynaklarına sahip ve doğrudan adreslenebilir Page RAM ile çalışan birimdir. Bir sonraki adım, bu Line'ın Group içindeki dört üyeyle nasıl eşgüdümleneceğini ve kaynakların nasıl paylaştırılacağını tanımlamaktır.
