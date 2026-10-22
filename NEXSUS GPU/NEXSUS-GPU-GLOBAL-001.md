# NEXSUS GPU — Global Group Manager ve Global Bus Manager

**Doküman Kodu:** `NEXSUS-GPU-GLOBAL-001`  
**Sürüm:** 0.1  
**Statü:** Kavramsal tasarım  
**Bağlı Dokümanlar:**
- `NEXSUS-GPU-ARCH-001`
- `NEXSUS-GPU-LINE-001`
- `NEXSUS-GPU-GROUP-001`

## 1. Amaç

Global yönetim katmanı, NEXSUS GPU içindeki birden fazla Group'un koordinasyonunu sağlar.

Mimaride iki temel yönetim birimi bulunur:

- **Global Group Manager (GGM):** Görevleri Group'lara dağıtır, Group'lar arasındaki bağımlılıkları ve kaynak tahsisini yönetir.
- **Global Bus Manager (GBM):** Group'lar arasındaki veri aktarımını, ortak kaynak erişimlerini ve veri yolu çakışmalarını yönetir.

Bu birimler birbirleriyle koordineli çalışır ancak farklı sorumluluklara sahiptir.

Temel ilke, Global Manager'ların bütün işlemleri merkezden yürütmesi değil, Group'ların bağımsız çalışmasını sağlayacak kararları vermesidir.

## 2. GPU yönetim hiyerarşisi

```text
                    NEXSUS GPU
                        |
            GLOBAL GROUP MANAGER
                        |
          +-------------+-------------+
          |             |             |
       GROUP 0        GROUP 1       GROUP N
          |             |             |
      Group Mgr.    Group Mgr.    Group Mgr.
          |             |             |
      4 Lines       4 Lines       4 Lines

            GLOBAL BUS MANAGER
                        |
        +---------------+---------------+
        |               |               |
   Group bağlantıları  Page RAM    Bellek arayüzleri
        |
   GPU ortak kaynakları
```

Bu şema işlevsel hiyerarşiyi gösterir. Global Group Manager ile Global Bus Manager'ın fiziksel yerleşimi, merkezi veya dağıtık kontrol yapısı daha sonraki tasarım aşamasında belirlenebilir.

## 3. Global Group Manager

Global Group Manager, GPU genelindeki görev dağıtımından ve Group'lar arası koordinasyondan sorumludur.

### 3.1 Görev dağıtımı

GGM, GPU'ya verilen işi yürütülebilir parçalara ayırır veya üst yazılım katmanının hazırladığı iş parçalarını uygun Group'lara atar.

Atama sırasında şu bilgiler dikkate alınır:

- Group'un kullanılabilir Line kapasitesi.
- Group'un mevcut iş yükü.
- Görevin ihtiyaç duyduğu işlem türleri.
- Verinin bulunduğu yer ve bellek erişim maliyeti.
- Görevler arasındaki veri bağımlılıkları.
- Görevin ihtiyaç duyduğu ortak kaynaklar.

Amaç yalnızca en az dolu Group'u seçmek değildir. Veri aktarım maliyeti yüksekse, daha az boş kapasiteye sahip ancak veriye yakın bir Group daha uygun olabilir.

### 3.2 Group durum tablosu

GGM, her Group'un durumunu izleyen bir durum tablosu kullanabilir.

Önerilen bilgiler:

| Alan | Amaç |
|---|---|
| Group ID | Group kimliği |
| Kullanılabilir Line sayısı | Atanabilecek yürütme kapasitesi |
| Aktif görev sayısı | Mevcut iş yükü |
| Bekleyen bağımlılıklar | İlerlemeyi etkileyen koşullar |
| Kaynak kullanımı | Bellek ve veri yolu gereksinimleri |
| Durum | Hazır, aktif, bekliyor veya kısıtlı |

Bu tablo mantıksal bir veri modelidir; nihai donanım tablosunun genişliği ve yapısı henüz belirlenmemiştir.

### 3.3 Group'lar arası görev bağımlılıkları

Bazı işler birden fazla Group'a bölünebilir.

Örneğin:

- Group 0 bir veri bloğunu işler.
- Group 1 başka bir veri bloğunu işler.
- Group 2 iki sonucun birleştirilmesini bekler.

Group 2'nin başlayabilmesi için gereken sonuçlar hazır değilse GGM bağımlılığı takip eder. Ancak bu durum Group 0 ve Group 1'in bağımsız çalışmalarını durdurmamalıdır.

Bağımlılık yönetimi, yalnızca gerekli işlerin bekletilmesini sağlamalıdır.

## 4. Global Bus Manager

Global Bus Manager, Group'lar ve GPU'nun ortak kaynakları arasındaki veri hareketini düzenler.

Başlıca görevleri:

- Group'lar arası veri aktarım taleplerini yönetmek.
- Page RAM ve GPU ortak kaynaklarına erişimi düzenlemek.
- Ortak veri yollarındaki çakışmaları çözmek.
- Aktarım önceliklerini ve kuyrukları yönetmek.
- Aktarımın tamamlandığı bilgisini ilgili birimlere iletmek.

GBM, Group içindeki her register erişimini veya yerel veri hareketini yönetmez. Bunlar mümkün olduğunca Line ve Group düzeyinde kalır.

### 4.1 Veri aktarım yolları

NEXSUS GPU'da veri aktarımı için birden fazla yol bulunabilir:

1. **Doğrudan Group bağlantısı:** Uygun ve sınırlı kapsamlı Group'lar arası aktarımlar.
2. **GPU ortak belleği veya Page RAM:** Daha geniş kapsamlı ve adreslenebilir veri paylaşımı.
3. **GPU dış bellek arayüzü:** Harici GPU belleğine erişim.
4. **GPU iç veri yolu:** Yerel bağlantıların yetmediği veya ortak kaynak gerektiren durumlar.

Her aktarımın aynı yolu kullanması zorunlu değildir. Veri boyutu, hedef, erişim sıklığı ve kaynak durumu uygun yolu belirlemeye yardımcı olur.

### 4.2 Veri yolu çakışmaları

Aynı kaynağa birden fazla Group erişmek istediğinde GBM talepleri sıralayabilir.

Önerilen değerlendirme ölçütleri:

- Veri bağımlılığı nedeniyle bekleyen işler.
- Gecikmeye duyarlı aktarımlar.
- Uzun süredir bekleyen talepler.
- Aktarımın veri yolu üzerinde kaplayacağı süre.
- Kaynak ve bellek erişim kuralları.

Öncelik sistemi, tek bir işin sürekli öncelik alarak diğerlerini süresiz bekletmesini önlemelidir. Gerekirse bekleme süresine dayalı öncelik artırımı uygulanabilir.

## 5. Global Group Manager ile Global Bus Manager ilişkisi

GGM işin **nerede ve ne zaman yürütüleceğine**, GBM ise gerekli verinin **hangi kaynak üzerinden ve hangi sırayla taşınacağına** odaklanır.

Örnek akış:

1. GGM bir görevi iki Group'a dağıtır.
2. Group'lar kendi Line'larında bağımsız yürütmeye başlar.
3. Bir Group başka bir Group'un sonucuna ihtiyaç duyar.
4. GBM gerekli veri aktarımını düzenler.
5. Sonuç hazır olduğunda ilgili bağımlılık güncellenir.
6. GGM, bekleyen işin devam edebileceğini belirler.

Bu süreçte GGM'nin her veri transferini kendisinin yönetmesi veya GBM'nin her görevin çalışma planını belirlemesi gerekmez.

## 6. Boşta kalan Line ve Group kapasitesi

NEXSUS GPU'nun dinamik kapasite kullanımı Group düzeyinde başlar ve GPU geneline uzanır.

Bir Group içindeki Line uygun başka bir iş bulamazsa, GGM başka Group'larda yürütülebilecek işler olup olmadığını değerlendirebilir. Ancak Line'ın doğrudan başka Group'a taşınması, fiziksel olarak aynı Line'ın iki Group'a birden ait olacağı anlamına gelmez.

İşin yeniden atanması sırasında:

- Mevcut register durumu korunmalı veya güvenli biçimde taşınmalıdır.
- Page RAM ve ortak bellek bağımlılıkları belirlenmelidir.
- Yeniden atamanın maliyeti hesaplanmalıdır.
- Yeni Group'un kaynakları ve bağlantıları uygun olmalıdır.

Bu nedenle her boşta kalan Line için görev taşımak zorunlu değildir. Yeniden atama yalnızca beklenen kazanç, taşıma ve koordinasyon maliyetlerini aştığında yapılmalıdır.

## 7. Global yönetimin darboğaza dönüşmesini önleme

Merkezi yönetim, sistemin tamamını her saat çevriminde denetlerse kendi başına bir darboğaz oluşturabilir.

Bunu önlemek için:

- Normal Line işlemleri yerel yürütülür.
- Group içi bağımlılıklar öncelikle Group Manager tarafından yönetilir.
- GGM yalnızca Group'lar arası görev ve kaynak kararlarına katılır.
- GBM, yalnızca ortak kaynak veya Group'lar arası aktarım gerektiren talepleri düzenler.
- Sık kullanılan durum bilgileri yerel olarak tutulabilir.
- Global yöneticilere gereksiz tekrar bildirimleri gönderilmez.

Yönetim katmanının dağıtık veya merkezi donanım olarak uygulanması henüz kararlaştırılmamıştır. Önemli olan mantıksal sorumlulukların ayrılmasıdır.

## 8. Hata ve kaynak kısıtları

Global yönetim, Group'un kapasitesinin azalması veya bir kaynağın geçici olarak kullanılamaması durumunda alternatif yerleşimi değerlendirebilir.

Örnek durumlar:

- Bir Group'ta bir Line devre dışı kalır.
- Bir bellek bankası geçici olarak yoğunlaşır.
- Bir veri yolu aşırı talep alır.
- Bir görev için gereken ortak kaynak uygun değildir.

GGM görevi başka bir Group'a yerleştirebilir veya yürütmeyi erteleyebilir. GBM ise aktarım yolunu değiştirebilir ya da erişimi sıralayabilir.

Bu işlevler, fiziksel yedeklilik veya otomatik hata kurtarmanın garanti edildiği anlamına gelmez. Bunlar ayrıca tasarlanmalı ve doğrulanmalıdır.

## 9. Tasarım sınırları

Henüz kesinleştirilmemiş başlıca parametreler:

- Group sayısı ve ölçeklenebilirlik sınırı.
- GGM görev kuyruğu ve zamanlama algoritması.
- GBM veri yolu topolojisi ve bant genişliği.
- Group'lar arası doğrudan bağlantıların sayısı.
- Ortak belleğin fiziksel yerleşimi.
- Global durum tablolarının boyutu ve güncellenme sıklığı.
- Görev yeniden atama maliyeti ve politikası.
- Kaynak öncelikleri ve adil erişim kuralları.

Bu değerler belirlenmeden kesin gecikme, güç tüketimi veya performans iddialarında bulunulmamalıdır.

## 10. Sonuç

NEXSUS GPU'nun global yönetim katmanı, Group'lar arası görev koordinasyonunu ve veri hareketini birbirinden ayırır.

Global Group Manager görevleri ve bağımlılıkları düzenler. Global Bus Manager ortak veri yollarını ve kaynak erişimini yönetir. Group Manager ve Group Bus Manager ise yerel çalışmayı sürdürür.

Bu hiyerarşi, bağımsız yürütme ve dinamik kapasite kullanımı hedeflerini destekler. Gerçek kazanımların belirlenmesi için sonraki aşamalarda görev zamanlama, bellek trafiği, veri yolu çakışmaları ve yeniden atama maliyetleri simülasyonla değerlendirilmelidir.
