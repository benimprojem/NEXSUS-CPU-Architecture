# NEXSUS GPU Group Fabric — Alıcı İçi Kuyruk Belleği ve Öncelikli Veri Yerleştirme

**Doküman Kodu:** `NEXSUS-GPU-GF-006`  
**Konu:** Alıcı birimlere gömülü küçük kuyruk belleği, FIFO okuma ve gönderici tarafında öncelik sıralaması  
**Statü:** Mimari karar taslağı — işlevsel kurallar belirleniyor, fiziksel uygulama henüz doğrulanmadı  
**İlişkili Belgeler:** `NEXSUS-GPU-GF-002`, `NEXSUS-GPU-GF-003`, `NEXSUS-GPU-GF-004`, `NEXSUS-GPU-GF-005`

---

## 1. Amaç

NEXSUS GPU Fabric içerisindeki veri aktarımında, alıcı birimin meşgul olması nedeniyle oluşan beklemeleri yönetmek için her alıcıya ait küçük bir kuyruk belleği kullanılması önerilmektedir.

Bu yaklaşımda kuyruk belleği, alıcıdan bağımsız büyük bir bellek alanında bulunmak zorunda değildir. Yeterince küçük olması durumunda doğrudan alıcı birimin donanım yapısına gömülebilir.

Temel hedefler:

- Bekleyen veriyi alıcıya yakın bir noktada tutmak.
- Merkezi Fabric üzerindeki kuyruk yönetimi yükünü azaltmak.
- Bağımsız alıcıların birbirini gereksiz yere bekletmesini önlemek.
- Öncelik sıralamasını veri tüketim mantığından ayırmak.
- Küçük ve öngörülebilir bir donanım yapısı oluşturmak.

## 2. Temel Mimari Karar

Her alıcı birim kendi yerel kuyruk belleğine sahip olur.

Örnek alıcılar:

- Line içindeki işlem birimleri.
- FP64 Engine.
- Matrix Engine.
- Group PRAM erişim arabirimi.
- Diğer uygun GPU hızlandırıcıları.

Her alıcının kuyruğu bağımsız yönetilir. Bir alıcının kuyruğunun dolması, başka bir alıcının kuyruğunun da dolduğu anlamına gelmez.

Kuyruk belleği alıcı birimin içine gömülü bir tampon olarak tasarlanabilir. Böylece ayrı bir kuyruk belleğine erişmek için ek bir bellek yoluna ihtiyaç duyulmaz. Bunun gerçek zamanlama, alan ve güç avantajı sağlayıp sağlamadığı fiziksel tasarım ve simülasyon aşamasında değerlendirilir.

## 3. Kuyruk Kapasitesi

Başlangıç tasarım hedefi, alıcı başına **4–8 kayıtlık yerel kuyruk** kullanılmasıdır.

Bu değer kesinleşmiş bir donanım parametresi değil, ilk işlevsel model için önerilen aralıktır.

Her kayıt, tasarıma göre aşağıdaki bilgileri içerebilir:

- Veri veya işlem komutu.
- Gerekli kaynak ya da hedef bilgisi.
- İşlem türü.
- Veri geçerliliği ve durum bilgisi.
- Gerekliyse bağımlılık veya işlem kimliği.

Kayıtların gerçek genişliği, her kuyruğun toplam bit kapasitesi ve kuyrukların ayrı ayrı mı yoksa ortak bir kayıt biçimiyle mi uygulanacağı henüz belirlenmemiştir.

Kuyruk kapasitesi, yalnızca bekleme ihtiyacını karşılayacak kadar küçük tutulmalıdır. Amaç büyük veri kümelerini depolamak değil, alıcı kısa süreliğine meşgul olduğunda aktarımın devamlılığını sağlamaktır.

Büyük veriler için Group PRAM veya ilgili veri belleği kullanılmaya devam edilir.

## 4. Gönderici Tarafında Öncelik Sıralaması

Öncelik değerlendirmesi gönderici tarafında veya Group Fabric'in gönderim planlama mantığında yapılır.

Birden fazla aktarım bekliyorsa, gönderici bunları önceliklerine göre sıralayarak uygun sırada alıcıya iletir.

Örneğin:

1. Yüksek öncelikli kontrol işlemi.
2. Kritik bağımlılığı bulunan veri.
3. Normal işlem verisi.
4. Daha düşük öncelikli arka plan işi.

Bu liste örnektir; kesin öncelik sınıfları daha sonra belirlenecektir.

Alıcı, göndericinin hangi öncelik hesabını yaptığını bilmek zorunda değildir. Alıcı kendisine yerleştirilen kayıtları sırayla tüketir.

### Önemli sınır

Öncelik sıralaması, yalnızca henüz gönderilmemiş veya henüz kuyruğa alınmamış işler arasında kolayca uygulanabilir.

Bir kayıt alıcının FIFO kuyruğuna yerleştirildikten sonra daha yüksek öncelikli bir kaydın onu geçmesi isteniyorsa, sırayı değiştirmek için ayrıca bir mekanizma gerekir. Bu tasarımın temel sürümünde böyle bir mekanizma bulunmaz.

Bu nedenle öncelik kararı, mümkün olduğunca kayıt alıcı kuyruğuna yazılmadan önce verilmelidir.

## 5. Alıcı Tarafında FIFO Okuma

Alıcı birimin okuma mantığı basit tutulur.

Alıcı:

1. Kuyruğun boş olup olmadığını kontrol eder.
2. Kuyruk boş değilse sıradaki kaydı okur.
3. Kaydı işleme alır.
4. Kayıt tüketildiğinde ilgili kuyruk alanını serbest bırakır.
5. Hazır olduğunda sonraki kaydı okur.

Alıcı, her kayıt için yeniden öncelik hesabı yapmak zorunda değildir.

Bu yapı, öncelik yönetimi ile veri tüketimini birbirinden ayırır. Alıcı tarafında daha basit bir kontrol mantığı oluşturmayı hedefler.

FIFO sırası, aynı kuyruğa yerleştirilmiş kayıtların sırasını korur. Farklı alıcılara ait kuyruklar ise birbirlerinden bağımsız çalışabilir.

## 6. Kuyruk Doluluğu ve Akış Kontrolü

Her kuyrukta en azından şu durumlar izlenmelidir:

- **EMPTY:** Kuyrukta okunacak kayıt yok.
- **AVAILABLE:** Yeni kayıt kabul edilebilir.
- **FULL:** Yeni kayıt kabul edilemez.
- **READING/CONSUMING:** Alıcı bir kaydı tüketiyor.

Bir kuyruğun dolması durumunda göndericiye veya Group Fabric'e kapasite bilgisinin iletilmesi gerekir.

Kuyruk doluyken yeni kayıt sessizce atılmamalıdır. Gönderim bekletilmeli veya yeniden planlanmalıdır. Kuyrukta yer açıldığında bekleyen aktarım devam edebilir.

Gerekli kapasite sinyali, hazır/meşgul bilgisi veya kredi tabanlı kontrol yöntemi daha sonraki fiziksel tasarım aşamasında seçilecektir.

## 7. Group Fabric ile İlişkisi

Group Fabric aşağıdaki görevleri sürdürür:

- Veriyi doğru alıcıya yönlendirmek.
- Alıcı kuyruğunun kapasitesini dikkate almak.
- Aynı kaynağı veya bağlantıyı isteyen aktarım taleplerini yönetmek.
- Gönderim sırasını ve öncelikleri belirlemek.
- Kuyruk doluluğunda akışı düzenlemek.
- Bağımsız kaynakların çalışmaya devam etmesini sağlamak.

Bununla birlikte her kayıt tüketimi için merkezi denetleyicinin yeniden karar vermesi zorunlu olmamalıdır. Rota ve aktarım izinleri belirlendikten sonra, alıcı kendi kuyruğunu yerel olarak tüketebilir.

Bu yaklaşım, merkezi Fabric'in gereksiz kontrol trafiğini azaltmayı amaçlar.

## 8. Bağımsız İlerleme İlkesi

Bir alıcının beklemesi, yalnızca o alıcıya veya ilgili kaynağa bağımlı işleri etkilemelidir.

Örnek:

- FP64 Engine A'nın kuyruğu dolu olabilir.
- Matrix Engine A kendi kuyruğundan işlem tüketmeye devam edebilir.
- FP64 Engine B, kendi alt grubuna ait bağımsız işlerini sürdürebilir.
- Başka bir Line, uygun kaynak ve veri bulunduğu sürece çalışmaya devam edebilir.

Bu davranış, NEXSUS GPU Fabric'in bağımsız kaynakları paralel çalıştırma hedefinin bir parçasıdır.

Ancak kaynaklar ortak bir bağlantıyı, Group PRAM bankasını veya bağımlı bir sonucu bekliyorsa, gerçek bir bekleme oluşabilir. Yerel kuyruklar tüm kaynak çakışmalarını ortadan kaldırmaz; yalnızca bekleyen kayıtların daha yerel ve kontrollü biçimde tutulmasını sağlar.

## 9. Sıralama ve Veri Bağımlılıkları

FIFO sırası, tek bir kuyruğa yazılan kayıtların sırasını korur. Farklı kuyruklar veya farklı kanallar üzerinden iletilen işler ise farklı zamanlarda ulaşabilir.

Bu nedenle:

- Aynı veri akışında sıralamanın korunması gerekiyorsa bu kural açıkça belirtilmelidir.
- Bağımlı bir işlem, gerekli veri hazır olmadan başlatılmamalıdır.
- Bağımsız işlemler sırf başka bir kuyrukta bekleme olduğu için durdurulmamalıdır.
- Birden fazla göndericinin aynı alıcı kuyruğuna yazması durumunda, kayıtların kabul sırasını belirleyen bir arbitraj mekanizması bulunmalıdır.

Öncelik sıralaması, veri bağımlılığı kurallarını geçersiz kılmaz.

## 10. Deadlock ve Aç Kalma Riski

Yerel kuyruklar küçük olsa da birden fazla kaynağın birbirini beklemesi hâlinde deadlock oluşabilir.

Örneğin, iki kaynak birbirinin kuyruğunda yer açılmasını veya birbirinden gelecek bir sonucu bekliyorsa, yalnızca kuyruk kapasitesi kullanmak sorunu çözmez.

İşlevsel modelde şu durumlar ayrıca test edilmelidir:

- Kuyrukların karşılıklı beklemesi.
- Yüksek öncelikli işlerin sürekli gelmesi nedeniyle düşük öncelikli işlerin aç kalması.
- Kuyruk doluyken kaynakların geri basınç uygulaması.
- Kuyrukta yer açıldığında aktarımın yeniden başlaması.
- Bağımsız alıcıların birbirinden etkilenmeden ilerlemesi.

Aç kalmayı önlemek için ileride bekleme süresine göre öncelik artırma veya sınırlı öncelik kullanımı değerlendirilebilir. Bu mekanizmalar temel tasarımda henüz kesinleştirilmemiştir.

## 11. İlk İşlevsel Simülasyon Planı

İlk simülasyon, 8 Line içeren bir Group üzerinde kurulmalıdır.

Test edilecek temel durumlar:

1. Boş kuyruğa kayıt yazılması ve FIFO sırasıyla okunması.
2. Dört kayıtlık kuyrukta doluluk davranışı.
3. Sekiz kayıtlık kuyrukta doluluk davranışı.
4. Farklı önceliklere sahip kayıtların gönderici tarafında sıralanması.
5. Kuyruk dolduğunda gönderimin bekletilmesi.
6. Bir kayıt tüketildiğinde yeni aktarımın devam etmesi.
7. Bir alıcının kuyruğu doluyken diğer alıcıların çalışmayı sürdürmesi.
8. Birden fazla göndericinin aynı alıcıya yönelmesi.
9. Bağımlı işlemlerin doğru sırada yürütülmesi.
10. Deadlock ve aç kalma senaryolarının kontrol edilmesi.

Bu testler, mimarinin işlevsel doğruluğunu değerlendirmek içindir. Fiziksel silikon performansını veya kesin çalışma frekansını kanıtlamaz.

## 12. Henüz Belirlenmemiş Parametreler

- Kuyruk başına kesin kapasite: 4 veya 8 kayıt ya da ihtiyaca göre farklı değer.
- Kayıt genişliği.
- Aynı anda okuma ve yazma davranışı.
- Bir alıcıya birden fazla göndericinin erişim yöntemi.
- Öncelik sınıfları ve eşit önceliklerdeki sıralama.
- Kuyruk doluluğunun bildirilme yöntemi.
- Kuyrukların fiziksel devre alanı ve güç maliyeti.
- Deadlock önleme ve aç kalma politikası.

Bu değerler ilk simülasyon ve sonraki donanım tasarımıyla belirlenmelidir.

## 13. Sonuç

NEXSUS GPU Fabric için önerilen model, **alıcıya gömülü küçük kuyruk belleği, gönderici tarafında öncelik sıralaması ve alıcı tarafında basit FIFO tüketimi** üzerine kuruludur.

Bu modelde:

- Alıcı, öncelik hesaplaması yapmak zorunda kalmaz.
- Bekleyen kayıtlar alıcıya yakın tutulur.
- Kuyruklar birbirinden bağımsız çalışabilir.
- Merkezi Fabric yönlendirme ve akış kontrolü görevlerini sürdürür.
- Kuyruk kapasitesi sınırlı tutularak bellek maliyeti kontrol altında tutulmaya çalışılır.

Bu tasarımın alan, güç ve gecikme avantajları henüz ölçülmüş değildir. Bir sonraki aşama, farklı kuyruk kapasitelerini ve eşzamanlı trafik durumlarını karşılaştıran işlevsel bir simülasyon oluşturmaktır.
