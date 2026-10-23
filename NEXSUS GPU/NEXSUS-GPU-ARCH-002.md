# NEXSUS GPU — Group Ölçeklendirmesi, L1/L2 Önbellek ve Kaynak Envanteri

**Doküman Kodu:** `NEXSUS-GPU-ARCH-002`  
**Konu:** Group tabanlı ürün ailesi, işlem kaynakları ve önbellek hiyerarşisi  
**Statü:** Mimari taslak — ölçeklendirme kararı belirlenmiştir, bellek parametreleri başlangıç hedefidir  
**İlişkili Belgeler:** `NEXSUS-GPU-ARCH-001`, `NEXSUS-GPU-GF-002` – `NEXSUS-GPU-GF-007`

---

## 1. Temel Ölçeklendirme Kararı

NEXSUS GPU ürün ailesi, Line sayısına göre değil, **Group sayısına göre** tanımlanacaktır.

Her Group sekiz Line içerir. Böylece her ürünün hesaplama kaynakları, bellek sistemi ve GPU Fabric kapasitesi Group sayısıyla ölçeklendirilebilir.

| Model | Group | Line | Hedef kullanım |
|---|---:|---:|---|
| NEXSUS G128 | 128 | 1.024 | Başlangıç modeli |
| NEXSUS G256 | 256 | 2.048 | Yüksek performans |
| NEXSUS G512 | 512 | 4.096 | Üst seviye |
| NEXSUS G1024 | 1.024 | 8.192 | En büyük ölçek |

Bu isimlendirmede G128, 128 Group anlamına gelir; 128 Line anlamına gelmez.

## 2. Group İçindeki Kaynaklar

Her Group aşağıdaki kaynakları içerir:

- 8 Line.
- Her Line için 8 FP16/FP32 çift modlu işlem aşaması.
- Her Line için 2 INT16 birimi ve 1 INT32 birimi.
- 2 FP64 Engine.
- 2 Matrix Engine.
- Her Line içinde yerel Line PRAM.
- Group çevresinde bankalı Group PRAM.
- Group içi trafik için Group Fabric.
- L1 önbellek ve önbellek kontrolü.

FP16/FP32 aşamaları ile INT birimleri ayrı kaynak sınıfları olarak sayılır. Registerlar ve operand tutucuları, temel kaynak sayımına ayrıca eklenmez.

## 3. Ürün Ailesi Kaynak Tablosu

| Kaynak | G128 | G256 | G512 | G1024 |
|---|---:|---:|---:|---:|
| Group | 128 | 256 | 512 | 1.024 |
| Line | 1.024 | 2.048 | 4.096 | 8.192 |
| FP16/FP32 işlem aşaması | 8.192 | 16.384 | 32.768 | 65.536 |
| INT16-A | 1.024 | 2.048 | 4.096 | 8.192 |
| INT16-B | 1.024 | 2.048 | 4.096 | 8.192 |
| INT32 | 1.024 | 2.048 | 4.096 | 8.192 |
| FP64 Engine | 256 | 512 | 1.024 | 2.048 |
| Matrix Engine | 256 | 512 | 1.024 | 2.048 |

FP16/FP32 sütunu, işlem aşamalarının sayısını gösterir; gerçek işlem hacmini veya NVIDIA CUDA çekirdekleriyle bire bir eşdeğerliği göstermez.

## 4. L1 Önbellek

L1, Line düzeyinde dağıtılmış yerel önbellek olarak tasarlanacaktır.

Başlangıç kapasite önerisi:

**16 KiB L1 önbellek / Line**

| Model | Line sayısı | Line başına L1 | Toplam nominal L1 |
|---|---:|---:|---:|
| G128 | 1.024 | 16 KiB | 16 MiB |
| G256 | 2.048 | 16 KiB | 32 MiB |
| G512 | 4.096 | 16 KiB | 64 MiB |
| G1024 | 8.192 | 16 KiB | 128 MiB |

Bu değerler, bütün Line'ların L1 kapasitesinin toplamıdır. Tek bir merkezi L1 belleği anlamına gelmez.

L1 önbelleğin görevleri:

- Sık kullanılan veriye düşük gecikmeli erişim sağlamak.
- Tekrarlanan veri erişimlerini azaltmak.
- Line'ın kendi hesaplama işlerini desteklemek.
- Uygun olduğunda yerel veri tekrar kullanımını artırmak.

L1; Line PRAM'ın, registerların veya Group PRAM'ın yerine geçmez. Bu bellekler farklı amaçlara hizmet eder.

## 5. L2 Önbellek

L2, Group'ların üzerinde çalışan GPU genel önbellek katmanı olacaktır. Group'lar arasında yeniden kullanılan verileri ve daha üst düzey bellek erişimlerini destekler.

G1024 modeli için başlangıç hedefi **128 MiB L2** olarak belirlenmiştir.

Daha küçük modeller için başlangıç ölçeklendirmesi:

| Model | Toplam L2 hedefi |
|---|---:|
| G128 | 16 MiB |
| G256 | 32 MiB |
| G512 | 64 MiB |
| G1024 | 128 MiB |

Bu değerler mimari başlangıç hedefleridir; zorunlu olarak tek bir fiziksel bellek bloğu oluşturulacağı anlamına gelmez.

Büyük modellerde L2'nin birden fazla fiziksel dilime ayrılması ve GPU Fabric üzerinden erişilmesi değerlendirilecektir. Dilim sayısı, bank sayısı, erişim genişliği ve yerleşim daha sonra belirlenecektir.

L2'nin görevleri:

- L1 önbellek kaçırmalarında daha üst düzey bir önbellek sağlamak.
- Group'lar arasında paylaşılan verilerin tekrar kullanılmasını kolaylaştırmak.
- GPU veri belleğine yapılan gereksiz erişimleri azaltmak.
- Grafik, hesaplama ve ışın izleme işlerinin ortak verilerine erişimi desteklemek.

L2'nin etkili olabilmesi için GPU Fabric'in erişim trafiğini ve olası banka çakışmalarını yönetmesi gerekir.

## 6. Bellek Hiyerarşisi

NEXSUS GPU'da bellek ve veri tutma katmanları aşağıdaki şekilde ayrılacaktır:

1. **Registerlar ve operand tutucuları:** Aktif işlemlerin anlık girdileri ve sonuçları.
2. **Line PRAM:** Line'a yerel programlanabilir veri ve ara sonuç alanı.
3. **L1:** Line düzeyinde önbellek.
4. **Group PRAM:** Aynı Group içindeki Line'ların paylaştığı bankalı bellek.
5. **L2:** GPU genel önbelleği.
6. **GPU veri belleği:** Büyük veri kümeleri, grafik kaynakları ve hesaplama verileri.
7. **GPU kod belleği:** GPU programları ve komutlar için ayrı bellek alanı.

Bu sıralama, her erişimin mutlaka tüm katmanlardan geçeceği anlamına gelmez. Erişim yolu veri türüne, bellek tutarlılığı kurallarına ve yürütme modeline göre belirlenmelidir.

## 7. GPU Fabric ve Önbellek Yönetimi

GPU Fabric yalnızca veri aktarımını değil, büyük GPU içindeki kaynakların ve bellek erişimlerinin yönetimini de üstlenir.

Temel görevleri:

- Group'lara iş dağıtımı.
- Group'lar arası veri yönlendirme.
- L2 dilimlerine erişim ve trafik yönetimi.
- Önbellek kaçırmalarının ilgili bellek katmanına yönlendirilmesi.
- Veri bağımlılıklarının korunması.
- Banka çakışmalarının ve kuyruk beklemelerinin yönetilmesi.
- Bağımsız işlerin gereksiz yere engellenmemesi.

G512 ve G1024 modellerinde tek bir merkezi bağlantı yapısının yeterli olup olmayacağı araştırılmalıdır. Bölgesel GPU Fabric katmanları, büyük tasarımlarda alternatif olarak değerlendirilecektir.

## 8. Grafik ve Özel İşlem Kaynakları

Line, Group ve önbellek sayıları GPU'nun tüm grafik kapasitesini tek başına belirlemez. Ürün ailesinde aşağıdaki kaynaklar ayrıca tanımlanacaktır:

- Rasterizer.
- Texture Mapping Unit (TMU).
- Render Output Unit (ROP).
- Ray Tracing Unit (RTU).
- Grafik komut ve iş dağıtım birimi.
- Video kodlama ve çözme birimleri.
- Görüntü çıkış denetleyicisi.

Bu birimlerin sayıları, bellek bant genişliği ve hedef çözünürlüklerle birlikte ölçeklendirilmelidir.

RTU sayısı için daha önce taslak olarak kullanılan G128=2, G256=4, G512=8 ve G1024=16 değerleri geçici hipotez olarak korunabilir; iş yükü simülasyonu olmadan kesinleştirilmemelidir.

## 9. Henüz Belirlenmemiş Parametreler

- Line PRAM kapasitesi ve sayfa boyutu.
- Group PRAM kapasitesi, banka sayısı ve port yapısı.
- L1 önbelleğin ilişkililik derecesi ve erişim politikası.
- L1 ile Line PRAM arasındaki veri paylaşımı kuralları.
- L2 dilim sayısı ve fiziksel yerleşimi.
- L1/L2 tutarlılık ve eşzamanlama kuralları.
- GPU veri belleğinin kapasitesi ve bant genişliği.
- GPU kod belleğinin kapasitesi.
- Bellek denetleyicisi ve kanal sayısı.
- TMU, ROP, rasterizer ve RTU kaynak sayıları.
- GPU Fabric'in fiziksel bağlantı genişliği, gecikmesi ve güç bütçesi.

## 10. Sonuç

NEXSUS GPU ürün ailesi Group tabanlı ölçeklendirme üzerine kurulacaktır. G128 başlangıç modeli, G1024 ise 1.024 Group ve 8.192 Line içeren büyük ölçekli model olacaktır.

L1 için Line başına 16 KiB, L2 için G128–G1024 arasında 16–128 MiB aralığı başlangıç tasarım hedefleri olarak belirlenmiştir.

Bu yapı, yerel hesaplama kaynaklarını, grup içi paylaşımı ve GPU genel veri erişimini ayrı katmanlarda ele alır. Sonraki aşamada önbellek, Group PRAM ve GPU veri belleğinin trafik simülasyonlarıyla birlikte değerlendirilmesi gerekir.
