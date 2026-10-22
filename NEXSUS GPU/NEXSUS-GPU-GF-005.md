**Doküman Kodu:** `NEXSUS-GPU-GF-005`  
**Konu:** Kuyruk yönetimi, geri basınç, kontrol mesajı önceliği ve ilerleme garantileri  
**Statü:** Mimari taslak — işlevsel kurallar tanımlandı, fiziksel parametreler açık

## 1. Amaç

Bu doküman, Group Fabric içindeki kontrol ve veri trafiğinin nasıl sıraya alınacağını, kaynakların doluluk durumunun nasıl yönetileceğini ve bir kaynağın meşgul olmasının bağımsız işleri gereksiz yere durdurmasını nasıl önlemeyi hedeflediğimizi tanımlar.

Tasarım, önceki kararları korur:

- İki adet 4-Line alt kümesi bulunur.
- Her alt küme kendi FP64 Engine ve Matrix Engine kaynaklarını kullanır.
- Alt kümeler arasında birden fazla bağımsız çift yönlü kanal vardır.
- Kanal seçimi kullanılabilirlik ve kuyruk durumuna göre yapılır.
- Kontrol ve veri trafiği ayrı mantıksal kuyruklarda yönetilir.
- Group PRAM bankalı ortak bellektir ve erişimleri Group Fabric üzerinden yönetilir.
- Bağımsız işler mümkün olduğunca paralel yürütülür.

## 2. Kuyruk sınıfları

Group Fabric mantıksal olarak üç kuyruk sınıfını yönetir.

### 2.1. Kontrol kuyruğu

İş tahsisi, aktarım talebi, kaynak durumu, senkronizasyon ve tamamlanma bildirimleri için kullanılır.

Kontrol mesajlarının amacı veri paketlerini taşımak değil, veri ve kaynakların nasıl kullanılacağını yönetmektir.

### 2.2. Veri aktarım kuyruğu

Alt kümeler arası veri akışları, paylaşılacak ara sonuçlar ve diğer Group içi aktarım talepleri için kullanılır.

Veri kuyruğundaki her talep hedefini, aktarım gereksinimlerini ve gerekiyorsa sıralama ilişkisini belirtmelidir.

### 2.3. Group PRAM erişim kuyruğu

Group PRAM okuma ve yazma talepleri bankalara göre düzenlenir.

Bir bankaya ait kuyrukta bekleme olması, bağımsız bankalara yapılan erişimleri otomatik olarak durdurmamalıdır.

Bu üç sınıf mantıksal ayrımdır. Fiziksel tamponların ve kuyrukların sayısı henüz kesinleşmemiştir.

## 3. Kuyruk doluluk takibi

Her kuyruk veya kaynak için kullanılabilir kapasite izlenmelidir.

Önerilen mantıksal durumlar:

- **Uygun:** Yeni bir talep kabul edilebilir.
- **Yoğun:** Yeni talepler kabul edilebilir, ancak kapasite yakından izlenmelidir.
- **Dolu:** Yeni talep veya veri, kapasite açılana kadar bekletilir.
- **Beklemede:** İstenen hedef veya sonraki aktarım kaynağı hazır değildir.

Bu durumlar belirli sayısal eşiklere bağlanmamıştır. Eşikler kuyruk kapasitesi, veri aktarım birimi ve hedef kaynak davranışı belirlendikten sonra tanımlanacaktır.

## 4. Geri basınç (backpressure)

Geri basınç, alıcı tarafında yeterli tampon veya kaynak bulunmadığında göndericinin yeni veri göndermesini sınırlayan mekanizmadır.

Temel kurallar:

1. Bir aktarımın hedefinde yeterli kapasite yoksa yeni veri gönderimi duraklatılabilir.
2. Kabul edilmiş veriler güvenli biçimde tutulmalı; normal akış kontrolü sırasında sessizce kaybedilmemelidir.
3. Geri basınç durumu göndericiye bildirilmelidir.
4. Hedefte kapasite yeniden açıldığında aktarım devam edebilmelidir.
5. Bir hedefin dolu olması, o hedefe bağlı olmayan diğer veri akışlarını gereksiz yere durdurmamalıdır.

Geri basınç, bütün sistemi durdurmak için değil, kapasitesi tükenen ilgili akışı düzenlemek için kullanılmalıdır.

## 5. Kontrol mesajlarının önceliği

Kontrol ve veri trafiği ayrı mantıksal kuyruklarda tutulur. Bununla birlikte, kontrol mesajlarına sınırsız öncelik verilmez.

Önerilen politika:

- Kritik akış kontrolü ve kaynak durumunu bildiren mesajlar zamanında işlenebilmelidir.
- Normal kontrol mesajları, veri trafiğinin ihtiyaçlarını da dikkate alan bir zamanlama politikasıyla gönderilmelidir.
- Veri aktarımı sürekli olarak kontrol mesajlarının arkasında bırakılmamalıdır.
- Sürekli kontrol trafiği, veri aktarımının sonsuza kadar beklemesine neden olmamalıdır.
- Veri aktarımının durması veya kaynakların dolması durumunda gereken kontrol mesajları ilerleyebilmelidir.

Kontrol mesajlarının öncelik sıralaması ve varsa rezervasyon mekanizması daha sonra ayrıntılandırılacaktır.

## 6. Bağımsız akışların ilerlemesi

Group Fabric, bir akışın beklemesinin diğer bağımsız akışları bloke etmesini önlemeyi hedefler.

Örnekler:

- Kanal A doluysa ve Kanal B uygunsa, bağımsız bir aktarım Kanal B üzerinden ilerleyebilir.
- Group PRAM Bank 0 bekliyorsa, Bank 1'e yönelen bağımsız bir erişim devam edebilir.
- Bir Line'ın Matrix Engine sonucu beklemesi, diğer alt kümedeki bağımsız işlemleri durdurmamalıdır.
- Bir hedefte geri basınç varsa, hedefe bağımlı olmayan işler mümkün olduğunca çalışmayı sürdürmelidir.

Bu davranış, kuyrukların ve kaynakların bağımsız yönetilmesini gerektirir. Gerçek uygulamada ortak fiziksel kaynaklar yine bir darboğaz oluşturabilir.

## 7. Kanal seçimi ve kuyruk yönetimi

Alt kümeler arası aktarım için Group Fabric şu sırayı izler:

1. Aktarım talebini alır.
2. Hedefi ve veri akışının sıralama gereksinimlerini belirler.
3. Kullanılabilir kanalları değerlendirir.
4. Kanal durumunu ve ilgili kuyruk doluluklarını kontrol eder.
5. Uygun kanala aktarımı atar.
6. Alıcı kapasitesi değişirse akışı duraklatır veya sürdürür.
7. Tamamlanma bilgisini ve kaynakların serbest bırakılmasını yönetir.

Kanal seçimi yalnızca en kısa kuyruğu seçmek zorunda değildir. Alıcı kapasitesi, aktarım bağımlılıkları ve kaynak uygunluğu da kararın parçası olabilir.

Belirli bir algoritma veya performans garantisi bu aşamada tanımlanmamıştır.

## 8. Deadlock ve sürekli bekleme riski

Geri basınç tek başına deadlock'u önlemez. Birden fazla aktarım birbirinin tamamlanmasını beklerken gerekli kaynaklar birbirini kilitleyebilir.

Bu nedenle sonraki modelde aşağıdakiler incelenmelidir:

- Kuyruk ve kaynak bağımlılıklarının döngü oluşturması
- Kontrol mesajlarının veri akışına bağımlı kalması
- Veri akışlarının karşılıklı olarak tampon beklemesi
- Aynı hedefi kullanan akışların sürekli birbirini engellemesi
- Bir işin sürekli olarak daha düşük öncelik nedeniyle bekletilmesi

Gerekirse ayrı mantıksal trafik sınıfları, rezervasyonlar, sanal kanallar veya belirli bir ilerleme garantisi veren kaçış yolu mekanizmaları değerlendirilebilir. Bunların sayısı ve fiziksel uygulanışı henüz kararlaştırılmamıştır.

## 9. Doğrulama planı

İlk işlevsel simülasyonda en az şu senaryolar bulunmalıdır:

1. Veri kuyruğunun dolması ve geri basınç uygulanması.
2. Kapasite açılınca bekleyen aktarımın devam etmesi.
3. Kontrol mesajlarının veri aktarımı yoğunken işlenebilmesi.
4. Veri akışının kontrol mesajları yüzünden sürekli beklememesi.
5. Bir kanal doluyken bağımsız başka bir kanalın kullanılabilmesi.
6. Bir Group PRAM bankı doluyken bağımsız bir bankaya erişimin sürmesi.
7. İki akışın karşılıklı kaynak beklemesiyle deadlock oluşturma ihtimali.
8. Bir akışın sürekli ötelenmesiyle starvation oluşma ihtimali.
9. Kaynaklar ve kuyruklar yoğunken bağımsız işlerin ilerlemesi.

Her testte beklenen davranış, model varsayımları ve gözlenen sonuçlar ayrı kaydedilmelidir.

## 10. Henüz belirlenmeyen parametreler

- Kuyruk sayısı ve kapasitesi
- Kontrol mesajı öncelik sınıfları
- Veri ve kontrol trafiği için tampon düzeni
- Geri basınç sinyalinin uygulanma biçimi
- Kanal başına kuyrukların fiziksel paylaşım modeli
- Rezervasyon ve kaynak tahsis kuralları
- Deadlock önleme veya kurtarma algoritması
- Starvation önleme politikası
- Gecikme, bant genişliği, alan ve güç değerleri

Bu parametreler kesinleşmeden fiziksel performans iddiasında bulunulmayacaktır.

## 11. Sonuç

NEXSUS GPU Group Fabric, kontrol ve veri trafiğini ayrı mantıksal kuyruklarda yönetir. Kuyruk doluluğunu izler, gerektiğinde geri basınç uygular ve bağımsız kanalların ve kaynakların mümkün olduğunca bağımsız çalışmasını hedefler.

Deadlock ve starvation riskleri, tasarımın sonraki doğrulama aşamasında ele alınacak zorunlu konulardır. Fiziksel kuyruk yapısı ve akış kontrol mekanizması, işlevsel modelin sonuçları görülmeden kesinleştirilmemiştir.