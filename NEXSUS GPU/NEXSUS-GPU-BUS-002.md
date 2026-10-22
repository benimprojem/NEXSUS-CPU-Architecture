# NEXSUS GPU — Global PR Veri Yolu ve Paralel Erişim Tasarımı

**Doküman Kodu:** `NEXSUS-GPU-BUS-002`  
**Sürüm:** 0.1  
**Statü:** Sayısal referans tasarım

## 1. Temel donanım kararları

Global PR için başlangıç değerleri aşağıdaki şekilde belirlenmiştir:

| Özellik | Referans değer |
|---|---:|
| Bağımsız banka sayısı | 32 |
| Banka kapasitesi | 16 KiB |
| Toplam Global PR | 512 KiB |
| Banka başına veri yolu | 128 bit |
| Okuma yolu | 128 bit |
| Yazma yolu | 128 bit |
| Dahili eşzamanlı erişim hedefi | 32 okuma + 32 yazma / çevrim |
| Harici erişim | 33. port |
| Hesaplama için örnek saat | 1 GHz |

Burada önemli karar, her bankanın okuma ve yazma işlemlerini ayrı veri yollarıyla desteklemesidir. Böylece aynı bankada okuma ve yazmanın aynı çevrimde yapılması hedeflenir.

Bu, tasarımın hedefidir; fiziksel bellek hücreleri, port yapısı ve zamanlama doğrulanmadan uygulanabilirliği kesinleşmiş sayılmaz.

## 2. Bir bankanın yapısı

Her Global PR bankası 16 KiB kapasiteye ve 128 bitlik veri yollarına sahiptir.

```text
               Global PR Bankası
              ┌──────────────────┐
Okuma isteği ─►│ Okuma denetimi   │──► 128-bit okuma yolu
              │                  │
              │    16 KiB PR     │
              │                  │
Yazma isteği ─►│ Yazma denetimi   │◄── 128-bit yazma yolu
              └──────────────────┘
```

Okuma ve yazma denetimleri ayrı mantıksal yollardır. Aynı bankaya aynı çevrimde iki istek geldiğinde:

- Okuma isteği okuma yolunu kullanır.
- Yazma isteği yazma yolunu kullanır.
- İki istek aynı adresle ilgiliyse okuma sonucunun eski veriyi mi yoksa yeni yazılan veriyi mi göstereceği ayrıca tanımlanır.
- Birden fazla yazma aynı adrese gelirse sıralama veya çakışma çözümü gerekir.

Bu yapı, tek portlu belleğe göre daha karmaşık olabilir. Belleğin fiziksel hücre tasarımı, iki ayrı erişim yolunu destekleyecek şekilde seçilmelidir.

## 3. Toplam dahili bant genişliği

128 bit = 16 bayt olduğuna göre, her banka bir çevrimde 16 bayt okuyabilir ve 16 bayt yazabilir.

32 banka için:

\[
32 \times 16 = 512\text{ bayt/çevrim}
\]

1 GHz örnek saatinde:

\[
512 \times 10^9
=512\text{ GB/s}
\]

Buna göre teorik bant genişliği:

| İşlem | 1 GHz örneğinde |
|---|---:|
| Okuma | 512 GB/s |
| Yazma | 512 GB/s |
| İki yönün toplamı | 1.024 GB/s |

Bu değerler, bütün bankaların her çevrimde bir 128 bitlik işlem gerçekleştirdiği varsayımına dayanır. Adres çatışmaları, bellek zamanlaması, ağ tıkanıklığı ve kontrol ek yükleri gerçek kullanımda erişilebilir bant genişliğini düşürebilir.

## 4. Saat frekansına göre kapasite

<Chart content={{"chartType":"bar","meta":{"title":"Global PR teorik bant genişliği","description":"32 banka × 128 bit × saat frekansı. Okuma ve yazma ayrı ayrı hesaplanmıştır; gerçek performans ölçümü değildir."},"xKey":"clock","series":[{"dataKey":"read","label":"Okuma","valueSuffix":" GB/s"},{"dataKey":"write","label":"Yazma","valueSuffix":" GB/s"}],"yAxisMin":0,"data":[{"clock":"500 MHz","read":256,"write":256},{"clock":"1 GHz","read":512,"write":512},{"clock":"1.5 GHz","read":768,"write":768},{"clock":"2 GHz","read":1024,"write":1024}]}} />

Bellek sisteminin 2 GHz'de çalışması zorunlu değildir. Saat frekansı; fiziksel yerleşim, bellek teknolojisi, güç tüketimi ve zamanlama analizinden sonra belirlenmelidir.

## 5. 33. harici port

Harici portu da başlangıçta 128 bitlik tam çift yönlü bir bağlantı olarak tanımlayalım:

- 128 bitlik bağımsız giriş yolu.
- 128 bitlik bağımsız çıkış yolu.
- Global PR banka adresi ve erişim kontrolü.
- Dahili erişimlerle çakışma yönetimi.

Bu referans modelde 1 GHz'de portun teorik kapasitesi her yönde 16 GB/s olur. Bu değer, GPU'nun harici sistem belleği bant genişliği değildir; yalnızca Global PR'nin 33. portuna ait örnek kapasitedir.

Dışarıdan erişim yapan birimler, bu port üzerinden Global PR'ye veri yazabilir ve okuyabilir. Harici portun protokolü ve elektriksel arayüzü ayrıca tanımlanacaktır.

### Harici erişim sırasında dahili paralellik

33. portun ayrı olması, dış erişimin 32 dahili bankanın kapasitesini otomatik olarak azaltmamasını sağlar. Ancak dışarıdan erişim yapılan banka aynı anda dahili olarak da kullanılıyorsa banka tasarımının iki erişimi karşılayabilmesi gerekir.

Bu nedenle banka denetleyicisi, okuma ve yazma portlarının yanı sıra harici erişimlerin önceliğini ve çakışma davranışını da yönetmelidir.

## 6. Fiziksel tasarım maliyeti

Bu mimarinin temel maliyeti yalnızca 512 KiB bellek kapasitesi değildir. 32 bankaya dağıtılmış okuma/yazma yolları ve bunları bağlayan ağ da önemli bir tasarım maliyeti oluşturur.

Özellikle:

- 32 bağımsız banka denetleyicisi gerekir.
- Okuma ve yazma için ayrı erişim yolları gerekir.
- Uzak Group erişimleri için yeterli bağlantı genişliği gerekir.
- 33. portun veri yolları ve kontrol mantığı ek alan kullanır.
- Bankalar ve yönlendiriciler arasındaki uzun bağlantılar güç ve gecikmeyi artırabilir.

Bu nedenle 1 TB/s üzerindeki toplam teorik aktarım kapasitesi, tek başına mimarinin verimli veya mevcut GPU'lardan üstün olduğunu göstermez. Aynı bant genişliğinin ne kadarının gerçek iş yüklerinde kullanılabildiği ölçülmelidir.

## 7. Doğrulama senaryoları

İlk simülasyon şu testleri kapsamalıdır:

1. Her bankaya aynı anda bir okuma isteği gönderilmesi.
2. Her bankaya aynı anda bir yazma isteği gönderilmesi.
3. 32 bankada eşzamanlı okuma ve yazma yapılması.
4. Dahili erişimlerle birlikte 33. porttan veri aktarılması.
5. Birden fazla Group'un aynı bankaya erişmesi.
6. Aynı adrese çakışan yazma ve okuma işlemleri.
7. Uzak bankalara erişim sırasında ağ tıkanıklığının ölçülmesi.

Ölçülecek sonuçlar; işlem verimi, gecikme, banka çatışmaları, güç tahmini ve bağlantı ağı üzerindeki yük olacaktır.

## 8. Sonraki tasarım kararı

Global PR için referans model artık 32 banka, banka başına 128 bit okuma ve yazma yolları ve 128 bitlik tam çift yönlü 33. port olarak tanımlanmıştır.

Bir sonraki adımda **Group PR'yi aynı ölçütlerle tasarlamalıyız**: dört Line'ın ortak kullandığı 32 KiB belleğin kaç bağımsız erişim yoluna sahip olacağı, Line'ların aynı anda nasıl okuyup yazacağı ve Global PR'ye ne zaman başvuracağı belirlenmelidir.