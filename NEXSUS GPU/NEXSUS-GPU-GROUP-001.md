# NEXSUS GPU — Dinamik Group Mimarisi

**Doküman Kodu:** `NEXSUS-GPU-GROUP-001`  
**Sürüm:** 0.2  
**Statü:** Kavramsal tasarım  
**Üst Mimari:** NEXSUS GPU — Dinamik Group Tabanlı Grafik İşlemci Mimarisi

## 1. Amaç

NEXSUS GPU Group, dört bağımsız Line'ın görev paylaşımı ve kaynak koordinasyonu yoluyla birlikte çalışmasını sağlayan temel işlem birimidir.

Group mimarisinin amacı yalnızca paralel işlem kapasitesini artırmak değildir. Aynı zamanda:

- Bağımsız Line'ların gereksiz yere birbirini beklemesini önlemek.
- Ortak görevlerde yalnızca gerekli noktalarda eşzamanlama yapmak.
- Boşta kalan Line kapasitesini mümkün olduğunda başka işlerde kullanmak.
- Register, Page RAM, ortak bellek ve veri yollarını verimli kullanmak.
- Yerel işlemleri Global Manager üzerinden geçirmek zorunda kalmadan koordinasyon sağlamak.

Temel tasarım ilkesi **bağımsız yürütme, bağımlılığa dayalı eşzamanlama ve dinamik kaynak kullanımıdır.**

## 2. Group yapısı

Her Group dört Line içerir:

- Line 0
- Line 1
- Line 2
- Line 3

Her Line kendi register havuzuna ve yürütme kaynaklarına sahiptir. Group içinde bir görevin paylaşılması, bu register havuzlarının fiziksel olarak tek bir havuza dönüştürülmesi anlamına gelmez.

```text
                    GROUP MANAGER
                          |
             +------------+------------+
             |            |            |
          Line 0        Line 1       ...
             |            |
             +----- GROUP -----+
             |                  |
      GROUP ORTAK BELLEĞİ   GROUP BUS MANAGER
             |                  |
             +--------+---------+
                      |
          GPU PAGE RAM / L1-L2 / BELLEK
```

Şema mantıksal ilişkileri gösterir. Group Manager ve Group Bus Manager ayrı işlevlerdir; fiziksel olarak tek bir kontrol bloğunda birleştirilebilirler.

## 3. Bağımsız yürütme modeli

Group içindeki Line'lar sürekli aynı komutu yürütmek zorunda değildir.

Her Line, kendisine atanmış komutları ve bağımlılıkları çerçevesinde bağımsız ilerler. Bir Line başka bir Line'ın sonucunu beklerken, bağımsız işi bulunan diğer Line'lar çalışmaya devam edebilir.

Örnek:

| Line | Görev | Durum |
|---|---|---|
| Line 0 | A verisini hesaplar | Çalışıyor |
| Line 1 | B verisini hesaplar | Çalışıyor |
| Line 2 | Line 0 sonucunu kullanacak | Bağımlılık bekliyor |
| Line 3 | Bağımsız C işlemini yürütür | Çalışıyor |

Line 2'nin beklemesi, diğer üç Line'ın da durmasını gerektirmez.

Eşzamanlama yalnızca aşağıdaki durumlarda gerekli olur:

- Bir Line'ın diğerinin ürettiği sonuca ihtiyacı varsa.
- Birden fazla Line ortak bir sonucu oluşturuyorsa.
- Ortak veriye erişimde sıralama veya tutarlılık gerekiyorsa.
- Görevin tamamlanması için belirlenmiş bir buluşma noktası varsa.

Eşzamanlama, bütün Group'u otomatik olarak durdurmamalıdır. Yalnızca ilgili bağımlılıklar ve kaynaklar etkilenmelidir.

## 4. Dinamik Line tahsisi

Group Manager, kullanılabilir Line'ları ve bekleyen işleri izler.

Bir görev dört Line'ın tamamını gerektirebilir; başka bir görev yalnızca bir veya iki Line kullanabilir. Kullanılmayan Line'lar, kaynaklar ve görev bağımlılıkları elverdiğinde farklı işlere atanabilir.

### Örnek: Yedi parçalı görev

İki Group, yedi bağımsız işlem parçasını yürütmek için tahsis edilsin.

| Group | Line | Atama |
|---|---|---|
| Group A | 0–3 | İlk dört işlem parçası |
| Group B | 0–2 | Sonraki üç işlem parçası |
| Group B | 3 | Uygun başka bir iş veya bekleme |

Son Line'ın başka işe atanması koşulsuz değildir. Atama yapılmadan önce şu noktalar kontrol edilir:

1. Yeni işin kullandığı register ve bellek kaynakları.
2. Aktif görevin bağımlılıkları.
3. Group ortak belleğine erişim çakışmaları.
4. Ortak veri yollarının kapasitesi.
5. İşlerin birbirinden güvenli biçimde ayrılabilmesi.

Bu kontroller sağlanırsa boşta kalan kapasite başka bir göreve ayrılabilir. Aksi durumda Line bekler.

## 5. Group Manager

Group Manager, Group içindeki görev koordinasyonunu yürütür.

### 5.1 Görev dağıtımı

- İş parçalarını uygun Line'lara atar.
- Hazır ve bekleyen işleri ayırt eder.
- Line kapasitesini ve mevcut görevleri izler.
- Yeni iş atamalarında kaynak çakışmalarını kontrol eder.

### 5.2 Bağımlılık yönetimi

- Üretici ve tüketici işlemler arasındaki bağımlılıkları takip eder.
- Bir sonucun ne zaman kullanılabilir olduğunu belirler.
- Gerekli olduğunda ilgili Line'ın ilerlemesini bekletir.
- Bağımsız işlerin yürütülmesini gereksiz yere durdurmaz.

### 5.3 Tamamlanma yönetimi

- Line görevlerinin tamamlanma durumunu takip eder.
- Ortak görevlerin bitiş koşullarını denetler.
- Sonuçların birleştirilmesi gereken durumları yönetir.
- Group kapasitesinin yeni görevlere açılabileceği zamanı belirler.

Group Manager her register erişimini veya her aritmetik işlemi yönetmez. Bunlar Line'ın yerel yürütme alanında kalır.

## 6. Group Bus Manager

Group Bus Manager, Group içindeki veri aktarımı taleplerini düzenler.

Görevleri:

- Line'lar arası doğrudan veri aktarımını koordine etmek.
- Group ortak belleği erişimlerini düzenlemek.
- Page RAM ve diğer ortak kaynaklara erişim taleplerini yönetmek.
- Çakışan erişimlerde öncelik ve sıralama uygulamak.
- Veri aktarımı için gerekli tamamlanma veya hazır sinyallerini sağlamak.

Bir veri yolu aynı anda bütün talepleri karşılayamıyorsa talepler sıraya alınabilir. Bu durumda bekleme süresi, kaynak kapasitesi ve erişim örüntüsüne bağlıdır.

Group Bus Manager'ın görevi bütün veri hareketlerini tek bir dar boğazdan geçirmek değildir. Yerel veya doğrudan bağlantıyla çözülebilecek aktarımlar gereksiz yere ortak yola yönlendirilmemelidir.

## 7. Ortak veri modeli

NEXSUS GPU Group üç veri paylaşım yöntemini destekleyecek şekilde tasarlanır.

### 7.1 Doğrudan Line'lar arası aktarım

Bir Line'ın ürettiği küçük bir sonuç, uygun olduğunda başka bir Line'a doğrudan aktarılabilir.

Avantajları:

- Page RAM'e yazıp yeniden okumayı önleyebilir.
- Küçük ve sık kullanılan sonuçlarda gecikmeyi azaltabilir.
- Ortak bellek üzerindeki trafik yükünü azaltabilir.

Sınırlamaları:

- Alıcı Line hazır değilse aktarım bekleyebilir.
- Birden fazla alıcı veya üretici varsa aktarım kaynakları paylaşılmalıdır.
- Veri bağımlılığı ve aktarımın tamamlanması doğru izlenmelidir.

Doğrudan aktarımın her veri için sınırsız ve eşzamanlı bağlantı sağlaması beklenmez. Bağlantı genişliği ve port sayısı fiziksel tasarım aşamasında belirlenir.

### 7.2 Group ortak belleği

Group ortak belleği, aynı Group içindeki birden fazla Line'ın erişebildiği küçük ve hızlı çalışma alanıdır.

Önerilen kullanım alanları:

- Sık paylaşılan ara sonuçlar.
- Birden fazla Line'ın kullandığı küçük veri kümeleri.
- İş parçaları arasındaki ortak çalışma verileri.
- Doğrudan aktarımın uygun olmadığı tekrar kullanılabilir veriler.

Ortak bellek, erişim çakışmalarına ve veri tutarlılığına ilişkin kurallar gerektirir. Bu alanın kapasitesi ve bank sayısı henüz sabitlenmemiştir.

### 7.3 Page RAM

Page RAM, doğrudan adreslenebilir uygulama çalışma belleğidir. Yalnızca önbellek veya register taşma alanı olarak değerlendirilmez.

Group içinde şu amaçlarla kullanılabilir:

- Daha büyük ara sonuç kümeleri.
- Birden fazla Line'ın ihtiyaç duyduğu çalışma verileri.
- Görevler arası paylaşılacak adreslenebilir veriler.
- Register kapasitesinin yeterli olmadığı durumlarda ek çalışma alanı.

Page RAM'in fiziksel yerleşimi GPU iç mimarisinin bir parçasıdır. Erişimler yerel önbelleklerden yararlanabilir; ancak Page RAM ile L1/L2 aynı işlevi taşımaz.

### Veri paylaşım yöntemlerinin karşılaştırması

| Yöntem | Öncelikli kullanım | Temel sınırlama |
|---|---|---|
| Doğrudan aktarım | Küçük, belirli üretici-tüketici sonuçları | Bağlantı ve port kapasitesi |
| Group ortak belleği | Aynı Group içinde tekrarlı paylaşım | Bank ve erişim çakışmaları |
| Page RAM | Daha geniş, adreslenebilir çalışma verileri | Erişim gecikmesi ve bant genişliği |
| L1/L2 önbellek | Tekrarlanan bellek erişimlerini hızlandırma | Önbellek isabeti ve tutarlılık politikası |

Bu yöntemler birbirini dışlamaz. Group Manager ve veri yolu kontrolü, uygun yöntemin kullanılmasını sağlar.

## 8. Register mimarisiyle ilişki

Her Line kendi register havuzunu korur. Group'lar birleştirilerek büyük bir görev yürütüldüğünde bu havuzlar fiziksel olarak birleşmez.

Bu nedenle:

- Sık kullanılan operandlar öncelikle yerel register'larda tutulur.
- Line'lar arası paylaşılan sonuçlar doğrudan aktarılabilir.
- Daha geniş paylaşılan çalışma verileri ortak bellekte veya Page RAM'de tutulabilir.
- Global Register Coordinator, gerekirse kullanılabilir register kapasitesini ve görev yerleşimini takip eder.
- Yerel register erişimleri global koordinatöre bağlı olmadan yürütülür.

Register sayısı, port sayısı ve ortak veri yolu genişliği, komut kümesi ve performans gereksinimleri belirlenince kesinleştirilecektir.

## 9. Global Group yönetimiyle ilişki

Birden fazla Group tek bir büyük görev için birleştirildiğinde her Group kendi yerel yöneticilerini korur.

**Global Group Manager:**

- Görevi Group'lara böler.
- Group'lar arasındaki bağımlılıkları takip eder.
- Group kapasitesi ve görev yerleşimini düzenler.
- Group'lar arası tamamlanma koşullarını koordine eder.

**Global Bus Manager:**

- Group'lar arasındaki veri aktarımını düzenler.
- Ortak bellek ve dış bağlantı taleplerini yönetir.
- Ortak veri yollarındaki çakışmaları kontrol eder.

Normal yerel işlemler Group yöneticilerinde kalır. Global yönetim, bütün işlemleri merkezden tek tek yürütmek yerine yalnızca Group'lar arası koordinasyon gereken durumlarda devreye girer.

## 10. Line durumları ve arıza yönetimi

Her Group, dört fiziksel Line'ın kullanılabilirlik durumunu Active Line Table (ALT) aracılığıyla takip edebilir.

Örnek durumlar:

- `READY`: İş almaya hazır.
- `RUNNING`: Aktif görev yürütüyor.
- `WAIT_DEP`: Veri bağımlılığı bekliyor.
- `WAIT_MEM`: Bellek veya veri aktarımı bekliyor.
- `DISABLED`: Kullanım dışı.

Bunlar önerilen mantıksal durum adlarıdır; nihai donanım kodlaması değildir.

Bir Line arızalandığında devre dışı bırakılması Group'un kapasitesini üç Line'a düşürebilir. ALT, arızayı izlemeye yardımcı olur ancak tek başına yedeklilik sağlamaz. Yedek Line, yeniden eşleme veya hata kurtarma mekanizmaları ayrı tasarım kararlarıdır.

## 11. Tasarım ilkeleri ve sınırlar

NEXSUS GPU Group şu ilkeler üzerine kuruludur:

1. **Bağımsız yürütme:** Line'lar gereksiz yere kilitlenmez.
2. **Bağımlılığa dayalı eşzamanlama:** Yalnızca ilgili işler veya kaynaklar bekletilir.
3. **Dinamik kapasite kullanımı:** Boşta kalan Line, uygun olduğunda başka göreve atanır.
4. **Çoklu paylaşım yolu:** Doğrudan aktarım, ortak bellek ve Page RAM birlikte kullanılır.
5. **Yerel kontrol:** Sıradan Line işlemleri Global Manager'a bağlı değildir.
6. **Kaynak güvenliği:** Yeni görev ataması bağımlılık ve kaynak çakışmalarını dikkate alır.
7. **Ölçülebilir tasarım:** Performans üstünlüğü simülasyon veya ölçümle doğrulanmalıdır.

Bağımsız görevlerin yeniden atanması, her durumda anında ve ücretsiz gerçekleşmez. Görev durumu, register içeriği, bellek bağımlılıkları ve bağlam yönetimi ek maliyet oluşturabilir. Dinamik atama, bu maliyetler dikkate alınarak uygulanmalıdır.

## 12. Henüz belirlenmemiş parametreler

Aşağıdaki ayrıntılar sonraki tasarım aşamalarında belirlenmelidir:

- Group ortak belleğinin kapasitesi ve bank yapısı.
- Doğrudan Line aktarım portlarının sayısı ve genişliği.
- Ortak veri erişimlerinde sıralama ve tutarlılık kuralları.
- Group Manager'ın görev kuyruğu ve yeniden atama politikası.
- Bağımlılık takibinin donanım tablosu ve kapasitesi.
- Group'lar arası veri yolu bant genişliği ve öncelik kuralları.
- Arızalı Line için yedekleme ve yeniden eşleme yöntemi.

Bu parametreler belirlenmeden kesin gecikme, alan, güç veya performans değerleri verilmemelidir.

## 13. Sonuç

NEXSUS GPU Group, dört Line'ın bağımsız yürütme kapasitesini korurken ortak görevleri koordine eden dinamik birimdir.

Mimarinin temel farkı, dört Line'ı sürekli aynı komut akışına bağlamak yerine görev bağımlılıklarını izleyerek gerektiğinde eşzamanlama yapmasıdır. Boşta kalan Line'ların başka işlerde kullanılması ve veri paylaşımı için birden fazla yol sunulması, kaynak kullanımını iyileştirmeyi hedefler.

Bu yaklaşımın gerçek performans kazanımları; görev dağıtımı, bellek gecikmeleri, veri yolu çakışmaları, ortak bellek yapısı ve donanım maliyetleri üzerinden doğrulanmalıdır.
