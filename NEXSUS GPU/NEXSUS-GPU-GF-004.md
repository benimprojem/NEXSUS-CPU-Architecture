# NEXSUS GPU Group Fabric — Çok Kanallı Bağlantı ve Trafik Yönetimi

**Doküman Kodu:** `NEXSUS-GPU-GF-004`  
**Konu:** Alt kümeler arası çok kanallı bağlantı, uyarlanabilir yönlendirme ve mantıksal trafik kuyrukları  
**Statü:** Mimari taslak — bağlantı davranışı kararlaştırıldı; fiziksel parametreler açık

## 1. Amaç

Bu doküman, NEXSUS GPU Group içindeki iki adet 4-Line alt kümesi arasında veri aktarımının nasıl yönetileceğini tanımlar.

Bağlantı modeli şu üç temel karara dayanır:

1. Alt kümeler arasında birden fazla bağımsız çift yönlü kanal bulunması.
2. Kanal seçiminin kullanılabilirlik ve kuyruk durumuna göre yapılması.
3. Kontrol ve veri trafiğinin ayrı mantıksal kuyruklarda yönetilmesi.

Bu kararlar bağlantının işlevsel davranışını tanımlar. Kanal sayısı, kanal genişliği, gecikme ve fiziksel performans henüz belirlenmemiştir.

## 2. Group içindeki kaynak düzeni

Her Group sekiz Line içerir ve iki adet 4-Line alt kümesine ayrılır.

- Alt küme A: Line 0–3, FP64 Engine A ve Matrix Engine A.
- Alt küme B: Line 4–7, FP64 Engine B ve Matrix Engine B.

Her alt küme kendi FP64 ve Matrix Engine kaynaklarını kullanır. Bir alt kümenin diğer alt kümenin işlem motorlarını kullanması mevcut tasarımda öngörülmemiştir.

Alt kümeler arası bağlantı veri paylaşımı içindir; ortak işlem motoru erişimi oluşturmaz.

Group PRAM, iki alt kümenin ortak belleğidir. Bellek bankalara bölünür ve erişimleri Group Fabric üzerinden yönetilir.

## 3. Çok kanallı bağlantı modeli

Alt kümeler arasındaki bağlantı, birden fazla bağımsız çift yönlü mantıksal kanaldan oluşacak şekilde tasarlanır.

Her kanalın iki yönde veri taşıyabilmesi amaçlanır. Böylece A'dan B'ye ve B'den A'ya aktarımlar desteklenir.

### Tasarım kuralları

- Birden fazla kanal bağımsız veri aktarım taleplerini taşıyabilmelidir.
- Group Fabric, uygun kanalı mevcut durumuna göre seçmelidir.
- Bir kanalın meşgul olması bütün aktarım kanallarının otomatik olarak durmasını gerektirmemelidir.
- Aktarım talebi için gerekli hedef ve veri hazır bilgileri kontrol edilmelidir.
- Hedef kaynak veya alıcı tarafı hazır değilse geri basınç uygulanabilmelidir.
- Kanal sayısı ve fiziksel bağlantı yapısı daha sonraki tasarım aşamasında belirlenmelidir.

“Bağımsız kanal” ifadesi, kanalların mantıksal olarak ayrı aktarım kaynakları olacağını belirtir. Kanalların fiziksel devrelerde ne ölçüde ayrılacağı henüz kararlaştırılmamıştır.

## 4. Uyarlanabilir kanal seçimi

Group Fabric, veri aktarımı için kullanılabilir kanalları değerlendirir ve kuyruk durumuna göre uygun kanalı seçer.

### Önerilen işleyiş

1. Bir aktarım talebi oluşur.
2. Group Fabric hedefi ve aktarım gereksinimlerini belirler.
3. Uygun kanalların kullanılabilirliği kontrol edilir.
4. Kuyruk durumu ve kaynak uygunluğu değerlendirilir.
5. Aktarım uygun kanala yönlendirilir.
6. Aktarım tamamlanınca ilgili kaynak ve kuyruk durumu güncellenir.

Kanal seçimi yalnızca en kısa kuyruğa bakmakla sınırlı olmak zorunda değildir. İleride hedefin hazır olması, kanalın kullanım durumu ve aktarımın sıralama gereksinimleri de seçim ölçütleri olabilir.

Bu algoritmanın ayrıntıları ve donanım maliyeti henüz belirlenmemiştir.

## 5. Kontrol ve veri trafiğinin ayrılması

Group Fabric içinde iki ayrı mantıksal trafik kuyruğu sınıfı tanımlanır.

### 5.1. Kontrol kuyruğu

Kontrol kuyruğu aşağıdaki mesajlar için kullanılır:

- İş ve kaynak tahsisiyle ilgili mesajlar
- Aktarım talebi ve hedef bilgileri
- Kaynak kullanılabilirliği ve durum bildirimleri
- Tamamlanma ve senkronizasyon bildirimleri
- Gerekli yönetim ve geri basınç mesajları

### 5.2. Veri kuyruğu

Veri kuyruğu aşağıdaki aktarım türlerini taşır:

- Line'lar arasında paylaşılan veriler
- Uygun forwarding yollarından yönlendirilemeyen ara sonuçlar
- Group PRAM erişimleriyle ilişkili veri aktarımı
- Alt kümeler arasında gerekli diğer veri akışları

Bu ayrım mantıksal düzeydedir. Kontrol ve veri kuyruklarının fiziksel olarak ayrı tamponlarda tutulup tutulmayacağı henüz kesinleşmemiştir.

Ayrı mantıksal kuyrukların amacı, uzun veri aktarımının kontrol mesajlarını aynı FIFO kuyruğunda bekletme riskini azaltmaktır. Bununla birlikte, ortak fiziksel kaynakların dolması hâlinde iki trafik sınıfı yine birbirini etkileyebilir.

## 6. Bağımsız işlerin yürütülmesi

Group Fabric'in temel politikası bağımsız işleri paralel yürütmektir.

Örneğin, A alt kümesinden B alt kümesine bir veri aktarımı sürerken:

- Diğer bağımsız bir aktarım uygun başka bir kanalı kullanabilir.
- B alt kümesindeki bağımsız bir Line işlemi çalışmaya devam edebilir.
- Group PRAM'in farklı bankalarına yönelen uygun erişimler birbirinden bağımsız yürütülebilir.
- Bir kaynak bekliyorsa, yalnızca ona bağımlı işler bekletilmeye çalışılır.

Bu davranış bir mimari hedeftir. Gerçek paralellik kanal kapasitesine, bellek banklarına, portlara, kuyruklara ve hedef kaynakların kullanılabilirliğine bağlı olacaktır.

## 7. Akış kontrolü ve sıralama

Çok kanallı aktarımda aşağıdaki konuların açıkça tanımlanması gerekir:

- Alıcının yeni veri kabul edebilmesi
- Kuyrukların doluluk durumunun izlenmesi
- Geri basınç ve yeniden deneme davranışı
- Aynı veri akışına ait mesajların sıralama gereksinimleri
- Bir aktarım tamamlandığında kaynakların serbest bırakılması
- Kanal değişiminin veri sıralamasına etkisi

Uyarlanabilir yönlendirme, bir veri akışının farklı kanallardan geçmesine izin verebilir. Bu nedenle mesajların sıralama garantileri ve gerekiyorsa yeniden sıralama mekanizması sonraki tasarım aşamasında ele alınmalıdır.

Deadlock riski de yalnızca kanal sayısıyla çözülmez. Kuyruklar, kaynak tahsisi ve akış kontrolü arasındaki bağımlılıklar birlikte incelenmelidir.

## 8. Fiziksel parametreler

Aşağıdaki değerler henüz belirlenmemiştir:

- Çift yönlü kanal sayısı
- Kanal başına veri yolu genişliği
- Kanalın fiziksel olarak ayrı veya paylaşımlı uygulanması
- Kontrol ve veri kuyruklarının tampon kapasiteleri
- Kuyruk başına desteklenen aktarım sayısı
- Kanal seçim algoritmasının ayrıntıları
- Veri sıralama ve yeniden sıralama mekanizması
- Aktarım gecikmesi
- Toplam bant genişliği
- Alan ve güç tüketimi

Bu parametreler belirlenmeden sayısal performans hedefleri veya fiziksel üstünlük iddiaları verilmemelidir.

## 9. İşlevsel doğrulama planı

İlk simülasyon modeli en az şu senaryoları kapsamalıdır:

1. A'dan B'ye ve B'den A'ya eşzamanlı aktarım.
2. Farklı kanallarda aynı anda bağımsız veri aktarımı.
3. Bir kanalın meşgul olması durumunda başka uygun kanalın seçilmesi.
4. Kanal kuyruklarının farklı doluluk seviyelerinde uyarlanabilir seçim.
5. Kontrol mesajlarının veri kuyruğundaki büyük aktarımlardan etkilenmesi.
6. Alıcı tarafının geri basınç uygulaması.
7. Bir akışın birden fazla kanala dağıtılmasının sıralama gereksinimlerine etkisi.
8. Bir kanal veya hedef kaynak beklerken bağımsız işlerin devam etmesi.
9. Kuyruk ve kaynak bağımlılıklarının deadlock oluşturup oluşturmadığının incelenmesi.

Simülasyon raporları, varsayılan parametreleri ve gözlenen sonuçları ayrı ayrı kaydetmelidir. İşlevsel doğrulama, fiziksel silikon performansını tek başına doğrulamaz.

## 10. Sonuç

NEXSUS GPU Group Fabric'in alt kümeler arası bağlantısı, birden fazla bağımsız çift yönlü kanala dayanır. Kanal seçimi kullanılabilirlik ve kuyruk durumuna göre yapılır. Kontrol ve veri trafiği ayrı mantıksal kuyruklarda yönetilir.

Bu tasarım, bağımsız işlerin paralel yürütülmesini ve bir bağlantıdaki beklemenin diğer bağımsız işleri gereksiz yere durdurmamasını hedefler.

Bir sonraki adım, Group Fabric'in kuyruk ve akış kontrol modelini tanımlamak; ardından bu modeli Group PRAM bankları ve üst GPU Fabric bağlantısıyla birleştirerek işlevsel simülasyona hazırlamaktır.
