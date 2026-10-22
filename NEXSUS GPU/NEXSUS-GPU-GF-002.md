# NEXSUS GPU Group Fabric ve Group PRAM Tasarımı

**Doküman Kodu:** `NEXSUS-GPU-GF-002`  
**Konu:** Group Fabric bağlantıları, Group PRAM bank yapısı ve erişim yönetimi  
**Statü:** Mimari taslak — temel kararlar belirlendi, fiziksel ayrıntılar geliştirme aşamasında

## 1. Amaç

Bu doküman, NEXSUS GPU mimarisindeki Group Fabric'in görevlerini ve Group PRAM erişim modelini tanımlar.

Her Group, sekiz Line içerir. Dört Line'lık her alt kümede bir FP64 Engine ve bir Matrix Engine bulunur. Dolayısıyla her Group'ta iki FP64 Engine ve iki Matrix Engine vardır.

Group Fabric, bu kaynaklar arasındaki iş dağıtımını ve veri akışını düzenler.

## 2. Kesinleşen mimari kararlar

1. **Line PRAM**, ilgili Line bloğunun içine yerleştirilir.
2. **Group PRAM**, onu kullanan Group'un çevresinde konumlandırılır.
3. Group PRAM, tek bir erişim bankası yerine bankalara bölünmüş ortak bellek olarak tasarlanır.
4. Line'ların Group PRAM erişimleri Group Fabric üzerinden yönetilir.
5. Group PRAM hem Line'lar arası veri alışverişi hem de ortak çalışma verileri ve ara sonuçların saklanması için kullanılır.
6. Register dosyaları, operand registerları ve giriş/çıkış tutucu registerları mevcut kabul edilir; temel kaynak sayımlarına ayrıca dahil edilmez.
7. Uygun bağımlı işlemler arasında doğrudan veri aktarımı desteklenir. Her ara sonucun PRAM'e yazılması zorunlu değildir.

## 3. Group Fabric'in görevleri

Group Fabric aşağıdaki işlevleri üstlenir:

- Line'lara iş ve kaynak tahsisi
- FP64 Engine ve Matrix Engine erişimlerinin düzenlenmesi
- İşlem bağımlılıklarının ve veri hazır durumunun takibi
- Line PRAM ile Group PRAM arasındaki erişimlerin yönetimi
- Group PRAM banklarının seçimi ve erişim çakışmalarının ele alınması
- Veri yönlendirme, geri basınç ve işlem tamamlama durumlarının yönetimi
- Üst GPU Fabric'e durum ve kaynak bilgisi sağlanması

Group Fabric bir veri yolu ile sınırlı değildir. Kontrol, zamanlama, kaynak yönetimi ve veri yönlendirme işlevlerini bir araya getiren yerel bir yönetim katmanıdır.

## 4. Group PRAM bank yapısı

Group PRAM, Group içindeki sekiz Line tarafından ortak kullanılan bir bellek alanıdır. Fiziksel olarak birden fazla bankaya bölünmesi öngörülür.

Bankaların sayısı, kapasitesi, veri genişliği ve port sayısı henüz belirlenmemiştir.

### 4.1. Erişim ilkeleri

- Farklı bankalara yönlendirilen bağımsız erişimler paralel yürütülmeye uygun olmalıdır.
- Aynı bankada çakışan erişimler algılanmalıdır.
- Çakışma durumunda ilgili erişimler uygun sırayla işlenmelidir.
- Bir bankadaki bekleme, bağımsız bankalara giden tüm erişimleri otomatik olarak durdurmamalıdır.
- Aynı adresi paylaşan okuma talepleri için yayınlama (broadcast) veya benzeri bir mekanizma ileride değerlendirilebilir.
- Aynı adrese eşzamanlı yazma durumunda sonuç belirsiz kalmamalıdır; yazma sıralaması ve senkronizasyon kuralları tanımlanmalıdır.

Bankalı bellek tasarımı tek başına belirli bir bant genişliği garantisi vermez. Erişim deseni, bank eşlemesi, port sayısı ve zamanlama davranışı ayrıca modellenmelidir.

## 5. Line PRAM ve Group PRAM arasındaki erişim

Line PRAM yerel çalışma alanıdır. Group PRAM ise birden fazla Line tarafından paylaşılan alandır.

Group PRAM'e erişim, Group Fabric tarafından yönetilir. Bu taslakta Line'lar arasında Group Fabric'i atlayan doğrudan Group PRAM erişim yolu tanımlanmamıştır.

### 5.1. Doğrudan veri aktarımı

Bir Line'ın ürettiği sonucu başka bir Line hemen kullanacaksa ve uygun forwarding yolu varsa veri doğrudan aktarılabilir.

### 5.2. Ortak bellek aktarımı

Bir sonuç birden fazla Line tarafından kullanılacaksa, daha sonra tekrar erişilecekse veya ortak çalışma verisi olarak tutulacaksa Group PRAM kullanılabilir.

Bu iki yöntem farklı amaçlara hizmet eder. Forwarding kısa bağımlılık zincirleri için; Group PRAM ise paylaşım ve saklama için değerlendirilir.

## 6. Kaynak ve çakışma yönetimi

Group Fabric, bir kaynağın meşgul olması nedeniyle yalnızca o kaynağa bağlı işlerin beklemesini hedefler.

Örneğin, bir Line'ın Group PRAM bankına erişimi çakışma nedeniyle bekliyorsa ve başka bir Line bağımsız bir FP işlemine devam edebiliyorsa, ikinci işlemin gereksiz yere durdurulmaması amaçlanır.

Bu davranış bir tasarım gereksinimidir. Gerçek uygulaması; kuyruklar, bağımlılık takibi, kaynak ayırma ve geri basınç mekanizmalarıyla geliştirilecektir.

## 7. Kontrol ağı ve veri ağı

Group Fabric'in mantıksal tasarımında iki işlev ayrılır:

### Kontrol işlevleri

- İş dağıtımı ve kaynak tahsisi
- Bağımlılık ve senkronizasyon takibi
- PRAM erişim taleplerinin düzenlenmesi
- Çakışma ve kaynak meşguliyetinin yönetimi
- İşlem durumu ve tamamlanma bildirimi

### Veri aktarımı işlevleri

- Line'lar arası veri iletimi
- Line PRAM ile Group PRAM arasındaki aktarım
- FP64 ve Matrix Engine veri yolları
- Uygun durumlarda doğrudan forwarding
- Üst GPU Fabric'e veya diğer Group'lara yönlendirilecek verilerin aktarımı

Bu ayrım başlangıçta mantıksal bir ayrımdır. Kontrol ve veri yollarının fiziksel olarak ayrı devreler olması henüz kararlaştırılmamıştır.

## 8. Henüz belirlenmeyen parametreler

Aşağıdaki konular sonraki tasarım aşamalarında değerlendirilecektir:

- Group PRAM kapasitesi
- Bank sayısı ve adres-bank eşleme yöntemi
- Bank başına okuma/yazma portları
- Aynı anda desteklenen erişim sayısı
- Veri genişliği ve hizalama kuralları
- Aynı adrese eşzamanlı yazma ve senkronizasyon kuralları
- Group içi bağlantı topolojisi
- FP64 ve Matrix Engine'lerin PRAM erişim yöntemi
- Group Fabric kuyruklarının kapasitesi
- Fiziksel alan, güç, gecikme ve bant genişliği tahminleri

Bu parametreler belirlenmeden kesin performans değerleri verilmemelidir.

## 9. Doğrulama yaklaşımı

Bir sonraki aşamada Group Fabric'in işlevsel modeli hazırlanmalıdır. İlk modelde en az şu senaryolar bulunmalıdır:

1. Farklı bankalara eşzamanlı erişim.
2. Aynı bankaya farklı adreslerden erişim çakışması.
3. Aynı adrese birden fazla okuma talebi.
4. Aynı adrese eşzamanlı yazma talepleri.
5. Bir Line'ın ürettiği sonucun başka Line'a forwarding ile aktarılması.
6. Group PRAM üzerinden paylaşılan verinin birden fazla Line tarafından kullanılması.
7. Bir kaynak beklerken bağımsız işlemlerin devam etmesi.
8. Group PRAM erişimleri ile FP64 ve Matrix Engine işleri arasındaki kaynak çakışmaları.

Simülasyon sonuçları, varsayımlar ve ölçülen değerler ayrı ayrı raporlanmalıdır. İşlevsel simülasyon, fiziksel silikonun gecikmesini veya bant genişliğini tek başına kanıtlamaz.

## 10. Sonuç

NEXSUS GPU Group Fabric, sekiz Line'lık Group'un işlem kaynaklarını ve ortak belleğini yöneten yerel kontrol ve veri yönlendirme katmanıdır.

Line PRAM yerel kalır; Group PRAM bankalara bölünmüş ortak bellek olarak tasarlanır ve erişimleri Group Fabric üzerinden yönetilir. Hem doğrudan veri aktarımı hem de ortak bellek kullanımı desteklenir.

Sonraki tasarım adımı, Group Fabric'in bağlantı topolojisini ve Group PRAM bank/port modelini işlevsel simülasyonla değerlendirmektir.