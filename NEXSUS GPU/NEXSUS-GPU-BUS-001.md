# NEXSUS GPU — Global PR Bağlantı Ağı ve Erişim Protokolü

**Doküman Kodu:** `NEXSUS-GPU-BUS-001`  
**Sürüm:** 0.1  
**Statü:** Referans tasarım

## 1. Tasarım hedefi

Global PR, GPU içinde fiziksel olarak dağıtılmış 32 bağımsız bellek bankasından oluşur. Her banka 16 KiB kapasitelidir ve toplam Global PR kapasitesi 512 KiB'dir.

Bağlantı ağı şu hedefleri karşılamalıdır:

- Farklı bankalara yapılan 32 bağımsız erişimin paralel yürütülebilmesi.
- Her Group'un gerekli Global PR bankasına erişebilmesi.
- Yakındaki bankalara kısa bağlantılarla erişim.
- Uzak erişimlerin diğer bankaların işlemlerini gereksiz yere durdurmaması.
- Dahili 32 erişim yoluna ek olarak 33. harici erişim portunun bulunması.
- Aynı bankaya çakışan erişimlerin düzenli biçimde yönetilmesi.

32 erişim hedefi, her bankanın uygun şekilde tasarlanması ve bağlantı ağının yeterli bant genişliği sağlaması koşuluna bağlıdır.

## 2. Bağlantı topolojisi

Referans model olarak **dağıtık Mesh bağlantı ağı ve yerel banka denetleyicileri** seçilmiştir.

Her Group ve Global PR bankası, uygun bir ağ düğümüne bağlanır. Düğümler arasındaki bağlantılar veri paketlerini hedef bankaya taşır.

```text
       Group A ── Group B ── Group C
          │          │          │
        Router ─── Router ─── Router
          │          │          │
       Bank 0     Bank 1      Bank 2
          │          │          │
       Banka denetleyicileri
          │
       Dağıtık Mesh ağı
          │
       ... 32 banka ...
          │
       Harici Port 33
```

Şema mantıksaldır; gerçek fiziksel yerleşimde her banka kendi konumuna yakın Groups ve ağ düğümleriyle ilişkilendirilebilir.

### Yerleşim kuralları

1. Global PR bankaları tek bir merkezi noktada toplanmaz.
2. Her banka kendi erişim denetleyicisine sahip olur.
3. Yakın Group erişimleri mümkün olduğunca az ağ adımı kullanır.
4. Uzak erişimler uygun ağ rotası üzerinden hedef bankaya iletilir.
5. Bir bankaya giden trafik, diğer bankalara giden trafiği zorunlu olarak engellemez.
6. Mesh düğümlerinin bağlantı kapasitesi, hedeflenen paralel erişim sayısını desteklemelidir.

## 3. Global PR adresleme

Her banka 16 KiB, yani 16.384 bayt kapasiteye sahiptir.

Bayt adreslemeli referans modelde:

- Banka kimliği için 5 bit gerekir: 32 banka.
- Banka içi adres için 14 bit gerekir: 16 KiB.
- Global PR toplam adres alanı 19 bittir.

Örnek mantıksal adres biçimi:

```text
┌─────────────────┬────────────────────────┐
│ Bank ID: 5 bit  │ Offset: 14 bit         │
└─────────────────┴────────────────────────┘
```

Bu biçimde:

- `Bank ID`, hedef bankayı belirler.
- `Offset`, banka içindeki bayt adresini belirler.

Toplam 19 bit, yalnızca Global PR'nin kendi adres alanı içindir; CPU veya GPU'nun genel adres genişliğini belirlemez.

Uygulamada banka kimliği adresin sabit üst bitlerinden üretilebilir veya erişim dağılımını iyileştirmek için adres bitleri karıştırılabilir. Nihai eşleme, gerçek iş yüklerinde banka çakışmalarını azaltacak şekilde seçilmelidir.

## 4. Banka erişim modeli

Her Global PR bankasının bağımsız erişim denetleyicisi bulunur.

Denetleyici şu işlemleri yürütür:

- Okuma ve yazma isteklerini kabul etmek.
- İstek adresini doğrulamak.
- Banka içi erişim zamanlamasını düzenlemek.
- Çakışan istekleri sıralamak.
- İşlem tamamlandığında sonucu isteği yapan birime iletmek.

### Referans banka çalışma hedefi

Her bankanın boru hatlı olarak tasarlanması ve uygun koşullarda her saat çevriminde yeni bir işlem kabul edebilmesi hedeflenir.

Bu hedef, her erişimin tek çevrimde tamamlanacağı anlamına gelmez. Bir işlem birden fazla çevrim sürebilir; boru hattı sayesinde önceki işlemler tamamlanmayı beklerken yeni işlemler kabul edilebilir.

## 5. 32 eşzamanlı erişim

Örnek olarak 32 Group'un her biri farklı bir Global PR bankasına birer erişim isteği gönderir.

| Durum | Beklenen davranış |
|---|---|
| 32 istek, 32 farklı banka | 32 işlem paralel yürütülebilir |
| 8 istek, aynı bankaya | Banka erişim kapasitesine göre sıraya alınabilir |
| Okuma ve yazma, farklı bankalara | Bağımsız bankalar üzerinden paralel yürütülebilir |
| Aynı adrese birden fazla yazma | Tanımlı sıralama ve tutarlılık kuralları uygulanır |
| Dahili ve harici istek, aynı bankaya | Banka denetleyicisi çakışmayı yönetir |

32 bankanın bulunması, her bankada aynı anda bir okuma ve bir yazmanın otomatik olarak mümkün olduğu anlamına gelmez.

**Temel hedef:** 32 farklı bankaya yapılan 32 bağımsız işlemin ortak bir merkezi denetleyici yüzünden seri hale gelmemesi.

## 6. 33. port — harici erişim

Harici port, Global PR'ye GPU dışından erişim sağlayan ayrı bir mantıksal arayüzdür.

Port 33 şu görevleri destekler:

- Global PR'ye veri yazmak.
- Global PR'den veri okumak.
- Erişim isteklerini hedef banka kimliğiyle ağa göndermek.
- Tamamlanan işlemlerin sonucunu dış birime iletmek.

Harici portun bağlantısı, GPU içindeki erişim ağını tek bir ortak dar boğaza dönüştürmemelidir.

Port 33'ün fiziksel arayüzü ve protokolü henüz belirlenmemiştir. Bu portun sistem belleği denetleyicisi, başka bir işlem birimi veya harici bir veri yolu ile bağlantısı sonraki tasarım aşamasında netleştirilecektir.

Harici erişimin yetkilendirme, bellek sahipliği ve eşzamanlı yazma kuralları da tanımlanmalıdır.

## 7. Okuma ve yazma politikası

İlk referans tasarımda her banka için şu davranışlar öngörülür:

- Bağımsız bankalara erişimler paralel yürütülür.
- Aynı bankaya gelen istekler banka denetleyicisi tarafından düzenlenir.
- Bir bankanın meşgul olması diğer bankaları otomatik olarak durdurmaz.
- Okuma ve yazma sırası, aynı adres için tutarlı sonuçlar verecek biçimde belirlenir.
- Aynı bankada eşzamanlı okuma ve yazma gerekiyorsa çift portlu bellek veya eşdeğer bir erişim düzeni ayrıca tasarlanır.

Bu aşamada bütün bankaların tek portlu mu, çift portlu mu olacağı kesinleştirilmemiştir. Bu karar, 32 dahili işlem hedefi ile 33. portun birlikte gerektirdiği bant genişliği hesaplandıktan sonra verilmelidir.

## 8. Erişim öncelikleri

Banka denetleyicisi ve ağ düğümleri, uzun süre bekleyen isteklerin sürekli ertelenmesini önlemelidir.

Önerilen öncelik kuralları:

1. Doğrulanmış ve geçerli istekleri kabul etmek.
2. Aynı banka üzerindeki çatışmaları çözmek.
3. Bekleme süresini dikkate alarak istekleri sıraya almak.
4. Harici portun dahili erişimleri sürekli engellemesini önlemek.
5. Acil erişim öncelikleri tanımlanırsa diğer istekler için adaletli hizmeti korumak.

Önceliklerin kesin sayısal değerleri henüz belirlenmemiştir.

## 9. Tasarım doğrulama planı

Bağlantı ağının başarısı yalnızca teorik port sayısıyla değerlendirilmemelidir. İlk simülasyonda şu senaryolar kullanılmalıdır:

- 32 farklı bankaya aynı anda okuma.
- 32 farklı bankaya aynı anda yazma.
- Okuma ve yazma işlemlerinin farklı bankalara dağıtılması.
- Bütün isteklerin tek bankada yoğunlaşması.
- 32 dahili işlemle aynı anda harici port erişimi.
- Yakın ve uzak Groups'un aynı bankalara erişmesi.
- Sürekli trafik altında bekleme süreleri ve erişim adaleti.

Ölçülecek sonuçlar:

- Eşzamanlı tamamlanan işlem sayısı.
- Banka başına işlem verimi.
- Ortalama ve en kötü bekleme süresi.
- Mesh üzerindeki trafik yoğunluğu.
- Harici portun dahili erişimlere etkisi.

## 10. Sonuç ve sonraki karar

NEXSUS GPU Global PR için referans model, 32 dağıtık banka, yerel banka denetleyicileri ve dağıtık Mesh bağlantı ağıdır. Harici erişim için 33. port bulunur.

Bu mimari, farklı bankalara yapılan bağımsız erişimlerin paralel yürütülmesini hedefler. Gerçek performans ise banka portları, veri yolu genişliği, yönlendirme ve fiziksel yerleşimle belirlenecektir.

**Sonraki tasarım adımı:** Her bankanın veri yolu genişliğini ve okuma/yazma port yapısını belirlemek; ardından 32 dahili erişim ile 33. harici portun aynı anda ne kadar veri taşıyabileceğini hesaplamak.
