# NEXSUS GPU Group Fabric — Bağlantı Topolojisi ve Kaynak Erişimi

**Doküman Kodu:** `NEXSUS-GPU-GF-003`  
**Konu:** Group içi Line bağlantıları, ortak işlem motorları ve alt kümeler arası veri aktarımı  
**Statü:** Mimari taslak — mantıksal bağlantı kararları belirlendi; fiziksel uygulama açık

## 1. Amaç

Bu doküman, NEXSUS GPU içindeki 8 Line'dan oluşan Group'un bağlantı topolojisini ve ortak kaynak erişim kurallarını tanımlar.

Group Fabric, Line'ların yerel işlem yolları ile Group düzeyindeki kaynaklar arasında kontrol, zamanlama ve veri yönlendirme görevlerini üstlenir.

## 2. Group yapısı

Her Group aşağıdaki kaynakları içerir:

- 8 Line
- Her Line için Line bloğuna gömülü Line PRAM
- 2 adet FP64 Engine
- 2 adet Matrix Engine
- Group çevresinde yerleşen bankalı Group PRAM
- Group Fabric kontrol ve veri yönlendirme mantığı

Group, iki adet 4-Line alt kümesine ayrılır.

| Kaynak | Alt küme A | Alt küme B |
|---|---|---|
| Line'lar | Line 0–3 | Line 4–7 |
| FP64 Engine | FP64 A | FP64 B |
| Matrix Engine | Matrix A | Matrix B |
| Line PRAM | Her Line içinde yerel | Her Line içinde yerel |
| Group PRAM | 8 Line tarafından ortak kullanılır | 8 Line tarafından ortak kullanılır |

Alt kümeler, işlem kaynaklarının yerel sahipliğini belirler. Group PRAM ise Group genelinde paylaşılan bir kaynaktır.

## 3. Kesinleşen bağlantı kararları

1. Her 4-Line alt kümesi kendi FP64 Engine'ine erişir.
2. Her 4-Line alt kümesi kendi Matrix Engine'ine erişir.
3. Bir alt kümenin diğer alt kümenin FP64 veya Matrix Engine'ini kullanması mevcut tasarımda desteklenmez.
4. İki alt küme arasındaki veri bağlantısı sınırlı ve Group Fabric tarafından yönetilen bir bağlantıdır.
5. Bağımsız işler paralel yürütülmelidir.
6. Bir kaynak veya veri yolu beklediğinde, bu kaynağa bağımlı olmayan işlerin gereksiz yere durdurulmaması hedeflenir.
7. Group PRAM bankalara bölünmüş ortak bellek olarak tasarlanır.
8. Group PRAM erişimleri Group Fabric üzerinden yönetilir.
9. Uygun bağımlı işlemler arasında doğrudan veri aktarımı kullanılabilir; ara sonuçların tümü için PRAM erişimi zorunlu değildir.


Her alt küme kendi dört Line'ı ile bir FP64 Engine ve bir Matrix Engine arasındaki erişimleri yönetir.

Group Fabric şu görevleri üstlenir:

- Ortak motorlara gelen işlem taleplerini düzenlemek
- Kaynak meşguliyetini takip etmek
## 4. Bağlantı katmanları

### 4.1. Line yerel katmanı

Her Line kendi işlem birimleri, register kaynakları ve Line PRAM'iyle yerel bir çalışma alanıdır.

Line içindeki uygun bağımlı işlemler doğrudan forwarding yoluyla birbirine bağlanabilir. Bu yerel davranış Group düzeyindeki bellek erişiminden ayrıdır.

### 4.2. 4-Line alt küme katmanı
- Aynı kaynağa eşzamanlı talepleri ele almak
- İşlem bağımlılıklarını takip etmek
- Bağımsız işlerin yürütülmesine izin vermek

FP64 ve Matrix Engine'lerin her Line'a ayrı fiziksel bağlantıyla mı, yoksa bir yerel anahtarlama ağıyla mı bağlanacağı henüz belirlenmemiştir.

### 4.3. Alt kümeler arası katman

Alt kümeler arasında sınırlı ve yönetilen veri aktarımı bulunur.

Bu tasarım, iki alt küme arasında bütün kaynakları doğrudan birbirine bağlayan tam çapraz bağlantıyı zorunlu kılmaz. Bunun yerine Group Fabric, gereken veri aktarımını mevcut bağlantı kaynakları üzerinden yönlendirir.

Bağlantı sayısı, veri yolu genişliği, kuyruk kapasitesi ve aynı anda yapılabilecek aktarım sayısı daha sonra belirlenecektir.

### 4.4. Group PRAM katmanı

Group PRAM, her iki alt kümenin Line'ları tarafından ortak kullanılır.

- Bellek bankalara bölünür.
- Group PRAM erişim talepleri Group Fabric tarafından yönetilir.
- Farklı bankalara yönlendirilen bağımsız taleplerin paralel yürütülmesi hedeflenir.
- Aynı banka veya port üzerinde çakışan talepler uygun şekilde sıraya alınır.
- Bağımsız bankalara yapılan erişimlerin bir bankadaki çakışma yüzünden gereksiz yere durdurulmaması amaçlanır.

Bank sayısı ve port modeli henüz kesinleşmemiştir.

## 5. Kontrol ve veri aktarımı

Group Fabric'in mantıksal görevleri iki ana işlev olarak ele alınır.

### Kontrol işlevi

- Kaynak tahsisi
- İşlem bağımlılığı takibi
- Ortak motor taleplerinin zamanlanması
- Group PRAM erişim taleplerinin düzenlenmesi
- Çakışma ve geri basınç yönetimi
- İşlem durumu ve tamamlanma bildirimi

### Veri aktarımı işlevi

- Line içi forwarding
- Line ile kendi alt kümesinin işlem motorları arasındaki veri akışı
- Alt kümeler arası yönetilen aktarım
- Line ile Group PRAM arasındaki erişim
- Group Fabric ile üst GPU Fabric arasındaki aktarım

Bu ayrım şimdilik mantıksaldır. Kontrol ve veri işlevlerinin fiziksel olarak ayrı donanımlar olması şart koşulmamıştır.

## 6. Eşzamanlı iş politikası

Group Fabric'in temel politikası bağımsız işleri paralel yürütmektir.

Örneğin:

- Line 1, kendi alt kümesinin Matrix Engine'ini kullanıyorsa Line 6'nın bağımsız bir işlem yapması engellenmemelidir.
- Bir Group PRAM bankındaki çakışma, başka bankaya yönelen bağımsız erişimleri otomatik olarak durdurmamalıdır.
- Bir Line'ın veri bağımlılığı nedeniyle beklemesi, diğer Line'ların tümünü durdurmamalıdır.
- Aynı motoru isteyen birden fazla işlem varsa, bu taleplerin sıralanması gerekir; ancak farklı kaynaklardaki işler bağımsız biçimde devam edebilmelidir.

Bu maddeler mimari hedeflerdir. Gerçek eşzamanlılık, bağlantı ve port sayısına bağlı olacaktır.

## 7. Örnek iş akışı

Line 2'nin kendi alt kümesindeki Matrix Engine ile bir işlem yaptığını ve sonucunu Line 6'nın kullanması gerektiğini düşünelim.

1. Line 2, Matrix Engine A'ya kendi alt kümesi üzerinden erişir.
2. İşlem sonucu üretilir.
3. Line 6'nın sonucu kullanabilmesi için gereken veri aktarımı belirlenir.
4. Uygun doğrudan aktarım yolu varsa veri bu yol üzerinden iletilir; aksi durumda Group Fabric tarafından yönetilen paylaşım yolu kullanılır.
5. Group PRAM gerekiyorsa sonuç ortak belleğe yazılır ve Line 6'nın erişim talebi Group Fabric tarafından yönetilir.
6. Veri hazır olduğunda Line 6 bağımlı işlemine devam eder.

Bu örnek, belirli bir gecikme veya bant genişliği varsaymaz. Fiziksel bağlantıların ve veri aktarım protokolünün ayrıntıları sonraki aşamada tanımlanacaktır.

## 8. Henüz belirlenmeyen noktalar

- Alt kümeler arası bağlantının fiziksel topolojisi
- Alt kümeler arası aktarım yolu sayısı
- Her aktarım yolunun veri genişliği
- Group PRAM bank sayısı ve port yapısı
- Group PRAM adres-bank eşleme yöntemi
- FP64 ve Matrix Engine giriş/çıkış kuyrukları
- Group Fabric kuyruk derinlikleri
- Çakışma çözümleme ve öncelik kuralları
- Group Fabric'in fiziksel alanı, güç tüketimi ve gecikmesi

Bu parametreler belirlenmeden fiziksel performans iddiasında bulunulmayacaktır.

## 9. Doğrulama planı

İşlevsel simülasyon aşağıdaki senaryoları içermelidir:

1. Aynı alt kümedeki birden fazla Line'ın kendi ortak işlem motoruna talepte bulunması.
2. İki alt kümenin kendi işlem motorlarını eşzamanlı kullanması.
3. İki alt küme arasında eşzamanlı veri aktarım talepleri.
4. Bir alt kümenin beklerken diğerinin bağımsız işlerine devam etmesi.
5. Farklı Group PRAM banklarına eşzamanlı erişim.
6. Aynı bankaya çakışan erişimlerin yönetilmesi.
7. Forwarding ile Group PRAM kullanımının karşılaştırılması.
8. Kaynak beklemelerinin bağımsız işlere etkisi.

Simülasyon çıktıları, model varsayımları ve ölçülen sonuçlar ayrı tutulmalıdır. İşlevsel modelin başarılı çalışması, fiziksel donanım performansının doğrulandığı anlamına gelmez.

## 10. Sonuç

NEXSUS GPU Group Fabric, sekiz Line'ı iki adet 4-Line alt kümesinde düzenler. Her alt küme kendi FP64 ve Matrix Engine kaynaklarını kullanır. Alt kümeler arasındaki veri aktarımı sınırlı ve yönetilen bağlantıyla sağlanır.

Group PRAM her iki alt kümenin ortak belleğidir ve erişimleri Group Fabric üzerinden yönetilir. Bağımsız işler paralel yürütülür; kaynak ve veri yolu çakışmaları yalnızca gerektiği ölçüde beklemeye neden olmalıdır.

Sonraki adım, alt kümeler arası yönetilen bağlantının mantıksal veri yolu sayısını ve Group PRAM banklarına erişim kurallarını belirlemektir. Fiziksel bağlantı ve performans parametreleri bu kararların ardından değerlendirilmelidir.