# NEXSUS GPU — PRAM, Group PRAM ve L1/L2 Bellek Hiyerarşisi

**Doküman Kodu:** `NEXSUS-GPU-MEM-003`  
**Konu:** Kod, ara sonuç ve veri beslemesi için çok katmanlı bellek mimarisi  
**Statü:** İşlevsel ayrım kararlaştırıldı; fiziksel parametreler geliştirme aşamasında  
**İlişkili Belgeler:** `NEXSUS-GPU-ARCH-001`, `NEXSUS-GPU-ARCH-002`, `NEXSUS-GPU-GF-002` – `NEXSUS-GPU-GF-007`

---

## 1. Temel Tasarım İlkesi

NEXSUS GPU'da bütün bellek türlerinin aynı işi yapması hedeflenmez. Kod saklama, ara sonuçları tutma, Group içi veri paylaşımı ve büyük veri kümelerine erişim ayrı katmanlara dağıtılır.

Bellek katmanlarının görevleri:

- **Line PRAM:** Çalışan kodlar ve ara sonuçlar.
- **Group PRAM:** Sekiz Line'a veri beslemesi ve Group içi paylaşım.
- **L1 Cache:** Kod ve veri için yerel önbellek.
- **L2 Cache:** GPU genelinde kullanılan büyük veri kümeleri için önbellek.
- **GPU veri belleği:** L2 kapasitesini aşabilen büyük veri kümeleri.
- **GPU kod belleği:** Program kodlarının ana saklama alanı.

Bu ayrım, küçük ve hızlı yerel alanların büyük veri kapasitesinden bağımsız tasarlanmasını sağlar.

## 2. Line PRAM

Line PRAM, her Line'ın içine gömülü programlanabilir yerel bellek olarak tanımlanır.

### Kapasite ve yapı

- Her Line için toplam hedef: **16 KiB**.
- Her Line'da iki bağımsız adreslenebilir sayfa.
- Başlangıç varsayımı: her sayfa 8 KiB.
- Her Line kendi PRAM alanına doğrudan erişir.
- Line PRAM erişimi, Group PRAM erişimiyle aynı yol üzerinden yürütülmek zorunda değildir.

İki sayfanın bulunması, bir sayfanın kod veya ara sonuçlarla kullanılırken diğerinin başka bir yerel veri kümesine ayrılmasına imkân verebilir. Sayfaların kullanım amacı yazılım ve yürütme modeline göre belirlenebilir; iki sayfanın sabit olarak biri kod, diğeri veri şeklinde ayrılması zorunlu değildir.

### Line PRAM toplam kapasitesi

| Model | Line sayısı | Toplam Line PRAM |
|---|---:|---:|
| G128 | 1.024 | 16 MiB |
| G256 | 2.048 | 32 MiB |
| G512 | 4.096 | 64 MiB |
| G1024 | 8.192 | 128 MiB |

Bu değerler, tüm Line'ların yerel PRAM kapasitelerinin toplamıdır.

## 3. Group PRAM

Group PRAM, aynı Group içindeki sekiz Line'ın ortak veri besleme ve paylaşım alanıdır.

### Banka yapısı

Her Group için:

- 8 bağımsız banka.
- Her banka için 32 KiB kapasite.
- Toplam 256 KiB Group PRAM.
- Erişim ve trafik yönetimi Group Fabric üzerinden yürütülür.

Her Line için ayrı bir banka tahsis etmek, sekiz Line'ın veri erişimini birbirinden daha bağımsız yönetebilmek amacıyla seçilmiştir. Bununla birlikte banka çakışmaları tamamen ortadan kalkmaz; birden fazla istek aynı bankaya yöneldiğinde erişimler sıraya alınabilir.

### Group PRAM kapasitesi

| Model | Group sayısı | Banka sayısı | Group başına kapasite | Toplam Group PRAM |
|---|---:|---:|---:|---:|
| G128 | 128 | 1.024 | 256 KiB | 32 MiB |
| G256 | 256 | 2.048 | 256 KiB | 64 MiB |
| G512 | 512 | 4.096 | 256 KiB | 128 MiB |
| G1024 | 1.024 | 8.192 | 256 KiB | 256 MiB |

Banka sayısı, toplam Group sayısının sekiz katıdır; çünkü her Group'ta sekiz banka bulunur.

### Görevleri

- Line'lara gerekli veriyi hızlı biçimde sağlamak.
- Aynı Group içindeki Line'lar arasında veri paylaşmak.
- Ara hesaplama sonuçlarının ortak kullanılmasını sağlamak.
- Büyük veri belleğine tekrar tekrar erişme ihtiyacını azaltmak.
- Group Fabric tarafından yönetilen bağımsız banka erişimlerini desteklemek.

Group PRAM, L1 önbelleğin yerine geçmez. Group PRAM açıkça adreslenen ve kontrol edilen bir çalışma alanıdır; L1 ise erişim geçmişine ve önbellek politikasına göre içerik tutar.

## 4. L1 Cache — Kod ve Veri

L1, Line'lara yakın çalışan ve hem komut kodlarını hem de verileri önbelleğe alabilen yerel katman olarak tanımlanır.

### Görevleri

- Yakın zamanda kullanılan kodlara hızlı erişim sağlamak.
- Sık kullanılan verileri yeniden kullanmak.
- L2 ve GPU veri belleğine giden gereksiz erişimleri azaltmak.
- Kod getirme trafiği ile veri erişim trafiğinin dengelenmesine yardımcı olmak.

### Kod/veri ayrımı

L1 içinde kod ve veri için mantıksal olarak ayrı alanlar veya ayrı erişim yolları kullanılabilir. Böylece veri trafiğinin komut getirmeyi gereksiz yere engellemesi azaltılabilir.

Ancak fiziksel kapasitenin sabit biçimde bölünmesi henüz kararlaştırılmamıştır. Başlangıç tasarımında şu seçenekler değerlendirilmelidir:

1. Kod ve veri için sabit kapasite bölüşümü.
2. Ortak L1 kapasitesi içinde dinamik kod/veri bölüşümü.
3. Kod ve veri için ayrı mantıksal önbellekler.

L1'in toplam kapasitesi, banka sayısı, satır boyutu ve eşzamanlı erişim sayısı simülasyon aşamasında belirlenecektir.

## 5. L2 Cache — Büyük Veri Önbelleği

L2, GPU genelinde erişilebilen ve esas olarak veri kümelerini önbelleğe almak için kullanılan ortak katmandır.

Line PRAM ve Group PRAM'ın aksine, L2'nin amacı belirli bir Line veya Group'a ait çalışma alanı sağlamak değil, GPU genelindeki veri tekrar kullanımını artırmaktır.

### Başlangıç kapasite hedefleri

| Model | L2 hedefi |
|---|---:|
| G128 | 16 MiB |
| G256 | 32 MiB |
| G512 | 64 MiB |
| G1024 | 128 MiB |

G1024 için 128 MiB L2, başlangıç tasarım hedefidir. L2'nin tek bir fiziksel blok olması zorunlu değildir; büyük modellerde birden fazla önbellek dilimi ve banka üzerinden dağıtılması değerlendirilecektir.

### Görevleri

- Group'lar arasında ortak kullanılan verileri önbelleğe almak.
- Büyük veri kümelerinin tekrar erişim maliyetini azaltmak.
- GPU veri belleğine giden trafiği azaltmak.
- Grafik, genel hesaplama ve ışın izleme verilerini desteklemek.

L2, bütün GPU verisini tutmak zorunda değildir. Veri kümeleri L2 kapasitesinden çok daha büyük olabilir; önbellek yalnızca uygun veri bloklarını tutar ve gerektiğinde değiştirir.

## 6. GPU Veri Belleği ve Kod Belleği

L2'nin dışında büyük kapasiteli GPU bellekleri bulunur.

### GPU veri belleği

Doku, geometri, görüntü tamponları, genel hesaplama dizileri ve diğer büyük veri kümelerini tutar.

Bu bellek için kapasite ve bant genişliği, Group sayısına ek olarak hedeflenen grafik çözünürlüğü, veri türleri ve eşzamanlı iş yükleriyle belirlenmelidir.

### GPU kod belleği

GPU programları ve komutlar için ayrı bir saklama alanı olarak tasarlanır.

Kod belleğinin kapasitesi genellikle veri belleğinden daha küçük olabilir. Bununla birlikte çok sayıda shader, program varyantı veya büyük hesaplama programı kullanıldığında kod kapasitesi de ölçülmelidir.

Kodun yürütme sırasında hangi bölümlerinin Line PRAM'a taşınacağı, L1'de önbelleğe alınacağı ve ana kod belleğinden getirileceği yürütme modelinin parçası olacaktır.

## 7. Bellek Katmanlarının Erişim İlişkisi

Bellek katmanları arasındaki ilişki aşağıdaki şekilde tanımlanır:

```text
GPU Kod Belleği ──► L1 Kod Alanı ──► Line PRAM ──► İşlem Birimleri

GPU Veri Belleği ──► L2 Veri Önbelleği ──► L1 Veri Alanı ──► Line

                                              │
                                              ▼
                                        Group PRAM
                                              │
                                  Sekiz Line arasında paylaşım
```

Bu şema, her erişimin bütün katmanlardan geçeceği anlamına gelmez. Örneğin, bir Line doğrudan kendi PRAM alanındaki bir ara sonucu kullanabilir; Group içindeki bir veri alışverişi Group PRAM üzerinden yapılabilir.

Group PRAM ve Line PRAM'ın önbelleklerle nasıl eşgüdümleneceği, aynı verinin birden fazla yerde bulunduğu durumlarda tutarlılık kuralları gerektirir. Bu kurallar ayrıca tanımlanmalıdır.

## 8. Önemli Tasarım Kuralları

1. Line PRAM, L1 ve Group PRAM birbirinin yerine geçmez.
2. Line PRAM her Line'a özeldir.
3. Group PRAM yalnızca ilgili Group içinde paylaşılır.
4. Group PRAM erişimleri Group Fabric tarafından yönetilir.
5. L1 hem kod hem veri için kullanılabilir.
6. L2, GPU genelindeki veri tekrar kullanımına odaklanır.
7. Büyük veri kümeleri GPU veri belleğinde tutulur; tamamının L2'ye sığması gerekmez.
8. Kod/veri ayrımı, gereksiz veri kopyalarını ve önbellek çakışmalarını azaltacak şekilde tasarlanmalıdır.
9. Aynı bankaya eşzamanlı erişimler ve önbellek kaçırmaları için kuyruk ve akış kontrolü bulunmalıdır.
10. Bellek kapasitesi toplamı, erişim bant genişliğinin yeterli olduğu anlamına gelmez; her ikisi ayrı değerlendirilmelidir.

## 9. Sonraki Doğrulama Aşaması

İlk bellek simülasyonunda aşağıdaki durumlar ölçülmelidir:

- Line PRAM'ın iki sayfasına eşzamanlı erişim.
- Sekiz Line'ın sekiz Group PRAM bankasına ayrı ayrı erişmesi.
- Aynı bankaya birden fazla erişim isteği gelmesi.
- L1 kod ve veri erişimlerinin birbirini etkilemesi.
- L1 kaçırmalarının L2'ye yönlendirilmesi.
- L2 kaçırmalarının GPU veri belleğine yönlendirilmesi.
- Birden fazla Group'ın ortak L2 dilimine erişmesi.
- Önbellek kaçırmaları ve veri tekrar kullanım oranları.
- Bellek kuyruğu doluluğu ve bağımsız işlerin ilerlemesi.

## Sonuç

NEXSUS GPU bellek mimarisi, kod saklama, yerel ara sonuçlar, Group içi veri paylaşımı ve GPU genel veri erişimini farklı katmanlarda ele alır.

Başlangıç parametreleri:

- Line PRAM: 16 KiB / Line, iki sayfa.
- Group PRAM: 8 banka × 32 KiB = 256 KiB / Group.
- L1: kod ve veri için yerel önbellek; kapasite ve bölümleme henüz açık.
- L2: G1024 için 128 MiB hedefi, daha küçük modellerde ölçekli kapasite.
- GPU veri belleği: büyük veri kümeleri için.
- GPU kod belleği: program ve komutların ana saklama alanı.

Bu parametreler işlevsel mimariyi tanımlamak için başlangıç noktasıdır. Fiziksel alan, gecikme, bant genişliği ve güç sonuçları simülasyon ve sonraki tasarım aşamalarıyla doğrulanmalıdır.
