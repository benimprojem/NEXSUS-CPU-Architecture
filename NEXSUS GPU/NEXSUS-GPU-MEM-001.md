# NEXSUS GPU — Çok Katmanlı Frekans ve Paralel Bellek Mimarisi

**Doküman Kodu:** `NEXSUS-GPU-MEM-001`  
**Konu:** GPU işlem frekansı, GPU Fabrik, yerel kod/veri belleği, banka yapısı ve veri yolu genişlikleri  
**Statü:** Ön mimari tasarım — doğrulama bekliyor  
**Sistem:** NEXSUS System Architecture

---

## 1. Amaç

NEXSUS GPU mimarisinin temel amacı, yalnızca işlem birimlerinin sayısını artırmak yerine işlem, bellek ve veri dağıtımı arasındaki darboğazları azaltmaktır.

Bu amaçla GPU üç temel frekans katmanına ayrılır:

- GPU işlem birimleri: **2 GHz**
- GPU Fabrik: **4 GHz**
- GPU'ya ait yerel kod ve veri belleği arayüzleri: **6 GHz**

Bu frekanslar ilk mimari tasarım hedefleridir. Nihai değerler, fiziksel tasarım, güç tüketimi, sinyal bütünlüğü ve bant genişliği testleriyle doğrulanacaktır.

## 2. Temel Mimari İlkeleri

1. GPU'nun kod belleği ve veri belleği birbirinden ayrıdır.
2. Her iki bellek de GPU'ya ait yerel fiziksel bellektir; CPU belleği ve Sistem Fabrik çevresindeki ortak sistem belleği bu kapasitelere dahil değildir.
3. GPU, ortak sistem belleğine gerektiğinde Sistem Fabrik üzerinden erişebilir.
4. Kod ve veri erişimleri mümkün olduğunca bağımsız yürütülür.
5. Bellek bankaları, farklı adreslere eş zamanlı erişimi destekleyecek biçimde düzenlenir.
6. GPU Fabrik, görevleri, bellek isteklerini ve işlem kümeleri arasındaki veri akışını koordine eder.
7. Register dosyaları işlem birimlerine yakın tutulur; sık kullanılan operandlar için düşük gecikme hedeflenir.
8. PRAM blokları, GPU Fabrik'in görev ve kontrol işlemlerini destekleyecek şekilde tasarlanır.

## 3. Frekans Katmanları

| Bileşen | Hedef frekans | Temel görev |
|---|---:|---|
| GPU işlem birimleri | 2 GHz | Grafik ve paralel hesaplama |
| GPU Fabrik | 4 GHz | Görev dağıtımı, kuyruklar ve bellek erişimlerinin koordinasyonu |
| Yerel kod belleği arayüzü | 6 GHz | GPU kodunun okunması |
| Yerel veri belleği arayüzü | 6 GHz | Veri okuma ve yazma |
| PRAM kontrol blokları | En az 4 GHz hedefi | Görev, adres, kuyruk ve durum bilgileri |
| Register dosyaları | 2 GHz işlem alanıyla uyumlu | Düşük gecikmeli operand erişimi |

Farklı frekanslarda çalışan bloklar arasında saat alanı geçişleri (clock-domain crossing), senkronizasyon ve tamponlama mekanizmaları gerekir. Frekans oranları tek başına gerçek bant genişliğini garanti etmez.

## 4. GPU Yerel Bellek Kapasiteleri

GPU kod ve veri bellekleri bağımsız kapasite seçenekleri olarak ele alınır.

| Konfigürasyon | Kod belleği | Veri belleği |
|---|---:|---:|
| GPU-S | 2 GB | 4 GB |
| GPU-M | 2 GB | 8 GB |
| GPU-L | 4 GB | 16 GB |
| GPU-XL | 6 GB | 32 GB |

Bu tablo başlangıç konfigürasyonlarını tanımlar. Kod ve veri kapasitesinin bağımsız seçilmesi, ileride farklı ürün kombinasyonlarına izin verir.

### 4.1. Kod belleği

Kod belleği, GPU tarafından yürütülecek shader programlarını, hesaplama çekirdeklerini ve diğer GPU programlarını tutar.

Kodun tamamının sürekli yerel bellekte bulunması zorunlu değildir. GPU, görev için gereken kodu gerektiğinde yükleyebilir ve kullanılmayan alanı yeniden kullanabilir.

Kod belleğinin temel özellikleri:

- Okuma ağırlıklı erişim.
- Çoklu banka üzerinden paralel kod okuma.
- Veri belleğinden bağımsız erişim denetimi.
- Kod yükleme, değiştirme ve geçersizleştirme yönetimi.

### 4.2. Veri belleği

Veri belleği; grafik geometrisi, dokular, görüntüler, video kareleri, hesaplama tamponları ve simülasyon verileri için kullanılır.

Temel özellikleri:

- Paralel okuma ve yazma.
- Bağımsız bellek bankaları.
- Okuma ve yazma istekleri için ayrı kuyruklar.
- Gerektiğinde ortak sistem belleğinden veri alma.
- Sonuçları belirtilen hedef adrese yazabilme.

Yerel veri belleği, GPU'nun bütün çalışma verisini tutmak zorunda değildir. Ancak sık kullanılan verilerin yerel bellekte bulunması, ortak Sistem Fabrik bağlantısındaki trafik ve gecikmeyi azaltabilir.

## 5. Bellek Bankası Mimarisi

### 5.1. Kod belleği bankaları

Başlangıç tasarımı:

- 8 banka.
- Banka başına 32 bitlik erişim genişliği.
- Toplam mantıksal erişim genişliği: 256 bit.

Bankalar bağımsız adreslere erişebilecek şekilde düzenlenir. Böylece farklı işlem kümeleri, erişimler farklı bankalara dağıldığında aynı anda kod okuyabilir.

Aynı bankaya gelen çakışan istekler sıraya alınır. Banka sayısı, tek başına aynı anda gerçekleştirilebilen okuma sayısını belirlemez; denetleyici ve veri yolu yapısı da bu kapasiteyi desteklemelidir.

### 5.2. Veri belleği bankaları

Başlangıç tasarımı:

- 32 banka.
- Banka başına 32 bitlik erişim genişliği.
- Toplam mantıksal erişim genişliği: 1024 bit.

Bu düzen, veri erişimlerinin farklı bankalara dağıtılmasını ve bağımsız işlemlerin paralel yürütülmesini hedefler.

Banka başına 32 bitlik erişim, bankanın toplam kapasitesi veya tüm bellek işlemlerinin her çevrimde mutlaka tamamlanacağı anlamına gelmez. Fiziksel bellek teknolojisi, erişim gecikmesi, burst uzunluğu ve kontrol devreleri ayrıca tanımlanmalıdır.

### 5.3. Banka dağıtımı

Banka seçimi, adres bitleri veya bir adres dağıtım fonksiyonu üzerinden yapılabilir.

Tasarımın hedefleri:

- Ardışık erişimlerin bankalara dengeli dağıtılması.
- Farklı bankalardaki isteklerin paralel işlenmesi.
- Aynı bankaya gelen isteklerin kontrollü biçimde sıralanması.
- Gereksiz banka çakışmalarının azaltılması.
- Kod ve veri trafiğinin ayrı denetim yollarında tutulması.

## 6. GPU Fabrik

GPU Fabrik, GPU içindeki işlem kümeleri ile yerel bellek denetleyicileri arasında görev ve veri akışını düzenleyen merkezi kontrol katmanıdır.

Başlangıç hedefleri:

- Saat frekansı: 4 GHz.
- GPU işlem birimleriyle görev koordinasyonu.
- Kod ve veri isteklerinin ayrı yönetimi.
- Görev kuyrukları ve önceliklendirme.
- Bellek bankalarına istek dağıtımı.
- İşlem kümelerinin durum takibi.
- Ortak Sistem Fabrik üzerinden dış bellek erişimlerinin koordinasyonu.

GPU Fabrik'in kontrol paketleriyle gerçek veri aktarımının aynı fiziksel bağlantıyı kullanması zorunlu değildir. Kontrol yolu ve geniş veri yollarının ayrılması, yüksek hacimli veri trafiğinin görev dağıtımını engellemesini önlemeye yardımcı olabilir.

## 7. Veri Yolu Genişlikleri

İlk tasarım adayları:

| Bağlantı | Genişlik | Frekans |
|---|---:|---:|
| Kod belleği arayüzü | 256 bit | 6 GHz |
| Veri belleği arayüzü | 1024 bit | 6 GHz |
| GPU Fabrik iç veri yolu | 1024 bit, çift yönlü | 4 GHz |
| İşlem kümesi veri yolu | 256–512 bit | 2 GHz işlem alanı |

İşlem kümesi veri yolu genişliği, işlem kümesi sayısı ve her kümenin register erişim gereksinimleri belirlendikten sonra kesinleştirilecektir.

GPU Fabrik'in 1024 bitlik çift yönlü yolu, her yönde bağımsız 1024 bit taşıyabilen bir yapı olarak tanımlanır. Fiziksel hat sayısı, yön başına genişlik ve saatleme yöntemi ayrıntılı donanım tasarımında netleştirilmelidir.

## 8. Teorik Bant Genişliği Hesapları

Basitleştirilmiş hesapta, her saat çevriminde bir aktarım ve sürekli dolu veri yolu varsayılmıştır.

Formül:

`Bant genişliği (GB/s) = Genişlik (bit) / 8 × Frekans (GHz)`

| Bağlantı | Genişlik | Frekans | Teorik bant genişliği |
|---|---:|---:|---:|
| Kod belleği | 256 bit | 6 GHz | 192 GB/s |
| Veri belleği | 1024 bit | 6 GHz | 768 GB/s |
| GPU Fabrik | 1024 bit/yön | 4 GHz | 512 GB/s/yön |

Bu değerler protokol yükünü, bekleme çevrimlerini, bellek gecikmesini, saat alanı geçişlerini veya erişim çakışmalarını içermez.

Ayrıca 6 GHz bellek saatinin bir çevrimde birden fazla aktarım gerçekleştiren bir arayüzde kullanılması durumunda gerçek aktarım hızı değişebilir. Nihai bant genişliği, fiziksel arayüz protokolü belirlendikten sonra hesaplanmalıdır.

## 9. Register ve PRAM Düzeni

### 9.1. Register dosyaları

Register'lar, GPU işlem kümelerinin doğrudan kullanacağı düşük gecikmeli çalışma alanıdır.

- İşlem birimlerine yakın yerleştirilir.
- Register dosyaları işlem kümeleri arasında dağıtılabilir.
- Eş zamanlı operand erişimi hedeflenir.
- Register bankası çakışmaları azaltılmalıdır.
- Register sayısı ve genişliği, işlem kümesinin paralellik gereksinimine göre belirlenmelidir.

### 9.2. PRAM

PRAM, GPU Fabrik'in görev kontrolü ve kısa süreli durum bilgileri için kullanılan programlanabilir hızlı bellek blokları olarak ele alınır.

Kullanım alanları:

- Görev tanımları.
- Kuyruk girdileri.
- Bellek istekleri.
- Adres ve boyut bilgileri.
- İşlem kümesi durumları.
- Senkronizasyon ve kontrol kayıtları.

PRAM için en az 4 GHz çalışma hedefi benimsenir. Bunun fiziksel olarak uygulanabilirliği, seçilen bellek hücresi ve denetleyici tasarımıyla doğrulanmalıdır.

PRAM kapasitesi ve port sayısı, GPU'nun toplam kod veya veri belleği kapasitesiyle karıştırılmamalıdır.

## 10. Görev ve Veri Akışı

1. CPU, GPU'ya görev tanımını ve gerekli adresleri gönderir.
2. GPU Fabrik görev paketini kabul eder ve uygun işlem kümesini belirler.
3. GPU, kodu yerel kod belleğinde kontrol eder; gerekirse kodu yükler.
4. GPU, veri adreslerini değerlendirir ve gerekli verileri yerel veri belleğinde kontrol eder.
5. Yerel bellekte bulunmayan veri gerekiyorsa Sistem Fabrik üzerinden talep edilir.
6. Veri hazır oldukça işlem başlatılır; bütün verinin önceden kopyalanması zorunlu değildir.
7. Sonuçlar hedef adrese yazılır.
8. Görev tamamlanma durumu CPU'ya bildirilir.

Bu yaklaşım, CPU'nun verileri önceden GPU belleğine taşımasını gerektirmeden adres tabanlı görev dağıtımını destekler.

## 11. Tasarımda Açık Kalan Konular

Bu belge frekansları, kapasite seçeneklerini ve başlangıç veri yolu genişliklerini belirler. Fiziksel tasarım için aşağıdaki konular ayrıca kararlaştırılmalıdır:

- GPU işlem kümesi sayısı.
- Küme başına işlem birimi ve register kapasitesi.
- Kod ve veri belleğinin fiziksel teknolojisi.
- Banka başına gerçek okuma/yazma portları.
- Bellek erişim gecikmeleri ve burst boyutları.
- GPU Fabrik'in kontrol yolu ile veri yolunun ayrımı.
- Saat alanı geçişleri ve senkronizasyon.
- Güç tüketimi, ısı ve fiziksel bağlantı maliyeti.
- Yerel bellek ile ortak sistem belleği arasındaki tutarlılık ve erişim kuralları.

## 12. Sonuç

NEXSUS GPU'nun ilk bellek mimarisi üç frekans katmanı üzerine kuruludur:

- 2 GHz işlem birimleri.
- 4 GHz GPU Fabrik.
- 6 GHz yerel kod ve veri belleği arayüzleri.

Kod belleği için 256 bitlik, veri belleği için 1024 bitlik başlangıç arayüzleri ve GPU Fabrik için 1024 bitlik çift yönlü iç veri yolu önerilmiştir.

Banka yapısı, bağımsız erişim ve görev dağıtımı birlikte tasarlanarak darboğazların azaltılması hedeflenmektedir. Bu değerler nihai donanım sonuçları değil, ayrıntılı mimari ve fiziksel fizibilite çalışmalarına temel oluşturacak tasarım hedefleridir.
