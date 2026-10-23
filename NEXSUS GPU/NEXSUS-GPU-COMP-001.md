# NEXSUS GPU ve NVIDIA RTX 5090: Mimari Ölçek, Hesaplama Kapasitesi ve Bellek Bant Genişliği Karşılaştırması

**Doküman Kodu:** `NEXSUS-GPU-COMP-001`  
**Konu:** NEXSUS GPU ürün ailesinin NVIDIA GeForce RTX 5090 ile mimari ve teorik performans karşılaştırması  
**Statü:** Mimari tasarım ve teorik hesaplama aşaması  
**Sürüm:** 1.0

---

## 1. Amaç

Bu dokümanın amacı, NEXSUS GPU mimarisinin G128, G256, G512 ve G1024 modellerini NVIDIA GeForce RTX 5090 ile karşılaştırmak ve geliştirilecek GPU ailesi için ölçülebilir tasarım hedefleri oluşturmaktır.

NEXSUS GPU tasarımı yalnızca hesaplama birimlerinin sayısını artırmayı hedeflemez. Temel amaç, çok sayıda bağımsız hesaplama kaynağının mümkün olduğunca aynı anda çalışabilmesini, bellek erişimlerinin paralelleştirilmesini ve işlem hatlarındaki gereksiz beklemelerin azaltılmasını sağlamaktır.

Karşılaştırma üç ana alanı kapsar:

- Hesaplama kaynaklarının ölçeklenmesi.
- Bellek kapasitesi, önbellekler ve bellek bant genişliği.
- GPU Fabric, Group yapısı ve paralel veri akışı.

**Önemli:** NEXSUS değerleri mimari hedeflere ve belirtilen varsayımlara dayalı hesaplamalardır. Fiziksel bir NEXSUS GPU henüz üretilmediği veya karşılaştırmalı olarak test edilmediği için gerçek uygulama performansı hakkında kesin sonuç çıkarılamaz.

## 2. NEXSUS GPU ürün ailesi

NEXSUS ürün isimlendirmesinde model numarası Group sayısını belirtir. Her Group sekiz Line içerir.

| Model | Group sayısı | Line sayısı |
|---|---:|---:|
| G128 | 128 | 1.024 |
| G256 | 256 | 2.048 |
| G512 | 512 | 4.096 |
| G1024 | 1.024 | 8.192 |

Her Group, iki adet dört-Line alt grubundan oluşur. Her dört-Line alt grubunun kendisine ait bir FP64 motoru ve bir Matrix Engine bulunur. Böylece her Group toplam iki FP64 motoru ve iki Matrix Engine içerir.

Alt gruplar kaynaklarını kendi çalışma alanlarında kullanır. Group Fabric, yönlendirme, kuyruklama, veri paylaşımı ve kaynak erişimini yönetir.

Bu yapı, model büyüdükçe hesaplama kaynaklarının düzenli biçimde artırılmasını sağlar.

## 3. Hesaplama kaynakları

Her Line aşağıdaki temel yürütme kaynaklarını içerir:

- Sekiz FP16/FP32 çift modlu yürütme aşaması.
- Bir INT16-A birimi.
- Bir INT16-B birimi.
- Bir INT32 birimi.
- Kod ve ara sonuçlar için Line PRAM.
- Veri aktarımını hızlandırmak için doğrudan sonuç iletimi (forwarding/bypass) desteği.

FP16 ve FP32 aynı aşamada birbirinden bağımsız iki ayrı hesaplama kapasitesi olarak sayılmaz. Aynı yürütme kaynakları farklı hassasiyet biçimlerinde çalışır.

### 3.1. Hesaplama kaynaklarının ölçeklenmesi

| Kaynak | G128 | G256 | G512 | G1024 |
|---|---:|---:|---:|---:|
| Line | 1.024 | 2.048 | 4.096 | 8.192 |
| FP16/FP32 yürütme aşaması | 8.192 | 16.384 | 32.768 | 65.536 |
| INT16-A | 1.024 | 2.048 | 4.096 | 8.192 |
| INT16-B | 1.024 | 2.048 | 4.096 | 8.192 |
| INT32 | 1.024 | 2.048 | 4.096 | 8.192 |
| FP64 motoru | 256 | 512 | 1.024 | 2.048 |
| Matrix Engine | 256 | 512 | 1.024 | 2.048 |

Bu tablo mimari kaynak sayılarını gösterir. Bir yürütme aşamasının fiziksel alanı, çevrim başına tamamladığı işlem sayısı ve desteklediği komutlar henüz silikon düzeyinde doğrulanmamıştır.

## 4. Karma hassasiyetli hesaplama

NEXSUS Flow, sonuç türü ve kayıt genişliği için tür kurallarına sahiptir. Programcı gerektiğinde kayıt genişliğini zorlayabilir; `!` işareti zorlamayı belirtir.

GPU mimarisi bu dil kurallarıyla uyumlu çalışmalıdır.

Örneğin FP16 operandlarla başlayan bir hesaplama, uygun sonuç yolu üzerinden FP32 olarak devam edebilir. Sonuç doğrudan bir sonraki aşamaya aktarılabiliyorsa PRAM'e yazıp yeniden okuma zorunluluğu oluşmaz.

Bu yaklaşımın amaçları:

- FP16 yürütme kaynaklarından yararlanmak.
- Gereken yerlerde FP32 ara sonuç ve biriktirme kullanmak.
- Bağımlı işlemlerde veri aktarım gecikmesini azaltmak.
- Bağımsız işlemlerin aynı anda yürütülmesini sürdürmek.

Daha yüksek hassasiyet gerektiren işlemler programcı tarafından açıkça seçilebilir. Otomatik genişletme ve zorlanmış genişlik davranışları dilin kurallarına göre uygulanır.

## 5. Bellek mimarisi

NEXSUS GPU, farklı görevleri olan bellek katmanlarına sahiptir.

| Bellek katmanı | Görev |
|---|---|
| Kayıtlar ve operand tutucuları | İşlemlerde kullanılan değerleri taşımak |
| Line PRAM | Kod ve ara sonuçları saklamak |
| L1 | Kod ve veriyi önbelleğe almak |
| Group PRAM | Aynı Group içindeki sekiz Line arasında veri paylaşmak |
| L2 | GPU genelindeki veriler için ortak, ağırlıklı olarak veri odaklı önbellek |
| GPU kod belleği | Programları ve komutları saklamak |
| GPU veri belleği | Büyük veri kümelerini saklamak |

Line PRAM ve Group PRAM, önbellekten farklı olarak açık adreslemeli kaynaklardır. Her erişimin bu katmanların tümünden geçmesi gerekmez; erişim yolu işlemin türüne ve bellek konumuna bağlıdır.

### 5.1. PRAM ve önbellek kapasiteleri

Line PRAM için her Line başına toplam 16 KiB ve iki bağımsız adreslenebilir sayfa varsayılmıştır. Bu varsayımda sayfa başına 8 KiB bulunur.

Group PRAM, her Group için sekiz banka ve banka başına 32 KiB olacak şekilde hedeflenmiştir. Böylece Group başına toplam 256 KiB elde edilir.

| Bellek | G128 | G256 | G512 | G1024 |
|---|---:|---:|---:|---:|
| Line PRAM toplamı | 16 MiB | 32 MiB | 64 MiB | 128 MiB |
| Group PRAM toplamı | 32 MiB | 64 MiB | 128 MiB | 256 MiB |
| L1 toplamı | 8 MiB | 16 MiB | 32 MiB | 64 MiB |
| L2 hedefi | 16 MiB | 32 MiB | 64 MiB | 128 MiB |

L1 toplam kapasitesi, Group PRAM toplamının dörtte biri olarak hedeflenmiştir.

L1 kod ve veri arasında dinamik paylaşılır. Kod veya veri taraflarından hiçbiri toplam L1 kapasitesinin %50'sinden fazlasını kullanamaz. Bu kural, bir tarafın diğerini tamamen dışlamasını önlemeyi amaçlar.

Bu değerler kapasite hedefidir; gerçek yonga alanı, güç tüketimi ve önbellek verimliliği henüz hesaplanmamıştır.

## 6. GPU veri belleği ve bant genişliği

Veri belleği, model büyüklüğüne göre ölçeklenir.

| Model | Veri belleği | Veri yolu genişliği | Pin başına veri hızı | Teorik bant genişliği |
|---|---:|---:|---:|---:|
| G128 | 12 GB | 256 bit | 20 Gbit/s | 640 GB/s |
| G256 | 16 GB | 256 bit | 20 Gbit/s | 640 GB/s |
| G512 | 24 GB | 512 bit | 20 Gbit/s | 1.280 GB/s |
| G1024 | 32 GB | 1.024 bit | 20 Gbit/s | 2.560 GB/s |

Teorik bant genişliği şu formülle hesaplanır:

\[
B=\frac{W\times R}{8}
\]

Burada:

- \(B\): teorik bant genişliği (GB/s).
- \(W\): veri yolu genişliği (bit).
- \(R\): pin başına veri hızı (Gbit/s).

Bu tabloda GB/s ondalık birim olarak kullanılır.

### 6.1. Varsayımsal etkin bant genişliği

İlk tasarım karşılaştırmasında %90 verimlilik varsayımı kullanılabilir.

| Model | Teorik bant genişliği | %90 varsayımsal etkin bant genişliği |
|---|---:|---:|
| G128 | 640 GB/s | 576 GB/s |
| G256 | 640 GB/s | 576 GB/s |
| G512 | 1.280 GB/s | 1.152 GB/s |
| G1024 | 2.560 GB/s | 2.304 GB/s |

%90 verimlilik henüz ölçülmüş bir sonuç değildir. Kod ve veri belleklerinin ayrılması, bağımsız bankalar ve paralel kanallar bellek çakışmalarını azaltabilir; ancak gerçek verimlilik erişim örüntülerine, denetleyicilere, bellek zamanlamasına ve fiziksel tasarıma bağlıdır.

## 7. Çift yönlü ve paralel bellek bağlantısı

NEXSUS GPU'nun temel ilkelerinden biri, tek bir veri yolunu olabildiğince hızlandırmaktan ziyade bağımsız aktarımların sayısını artırmaktır.

G1024 için hedeflenen toplam veri yolu genişliği 1.024 bittir. Bunun bağımsız kanallara ve bankalara bölünmesi değerlendirilmelidir.

Örnek bir düzen:

- 16 bağımsız kanal.
- Kanal başına 64 bit veri genişliği.
- Toplam 1.024 bit veri yolu.
- Kanal ve bellek bankalarının mümkün olduğunca bağımsız çalışması.
- Okuma ve yazma trafiğinin, fiziksel bellek arayüzünün desteklediği ölçüde paralel yürütülmesi.

GPU Fabric, bellek isteklerini hedeflerine göre dağıtır. Bir bankadaki bekleme, bağımsız bir bankanın işlemini durdurmamalıdır. Kuyruklar dolduğunda veri kaybı yerine geri basınç uygulanır.

1.024 bitlik toplam genişlik, tek başına 1.024 bağımsız kanal anlamına gelmez. Gerçek paralellik kanal denetleyicilerine, bankalara ve erişimlerin bağımsızlığına bağlıdır.

## 8. NVIDIA RTX 5090 ile teknik karşılaştırma

RTX 5090 için referans alınan başlıca teknik değerler:

- 21.760 CUDA çekirdeği.
- 32 GB GDDR7 bellek.
- 512 bit bellek arayüzü.
- 1.792 GB/s teorik bellek bant genişliği.
- 96 MiB L2 önbellek.
- 575 W toplam grafik kartı gücü.
- 170 SM.

RTX 5090'ın mimarisi, özel Tensor Core ve RT Core kaynakları dahil olmak üzere farklı yürütme türlerine sahiptir. NEXSUS'un Line, Matrix Engine ve RTU kaynakları bu birimlerle bire bir eşdeğer değildir.

| Özellik | G128 | G256 | G512 | G1024 | RTX 5090 |
|---|---:|---:|---:|---:|---:|
| Line sayısı | 1.024 | 2.048 | 4.096 | 8.192 | Doğrudan eşdeğer yok |
| FP16/FP32 aşaması | 8.192 | 16.384 | 32.768 | 65.536 | 21.760 CUDA çekirdeği |
| FP64 motoru | 256 | 512 | 1.024 | 2.048 | SM içindeki FP64 kaynakları |
| Matrix Engine / Tensor Core | 256 | 512 | 1.024 | 2.048 | 680 Tensor Core |
| Veri belleği | 12 GB | 16 GB | 24 GB | 32 GB | 32 GB |
| Bellek veri yolu | 256 bit | 256 bit | 512 bit | 1.024 bit | 512 bit |
| Teorik bant genişliği | 640 GB/s | 640 GB/s | 1.280 GB/s | 2.560 GB/s | 1.792 GB/s |
| L2 | 16 MiB | 32 MiB | 64 MiB | 128 MiB | 96 MiB |
| GPU frekansı | 2 GHz hedef | 2 GHz hedef | 2 GHz hedef | 2 GHz hedef | Yaklaşık 2,01 GHz temel, 2,41 GHz boost |
| Kart gücü | Belirlenmedi | Belirlenmedi | Belirlenmedi | Belirlenmedi | 575 W |

**Not:** NEXSUS FP16/FP32 aşamaları ile NVIDIA CUDA çekirdekleri farklı mimari tanımlardır. Kaynak sayılarının karşılaştırılması, eşdeğer işlem gücünü veya gerçek performans üstünlüğünü kanıtlamaz.

## 9. Teorik hesaplama kapasitesi

İlk hesaplama modeli aşağıdaki varsayımları kullanır:

- Her Line'da sekiz FP16/FP32 yürütme aşaması bulunur.
- GPU frekansı 2 GHz'dir.
- Her aşama FP32 modunda çevrim başına bir işlem tamamlar.
- Her aşama FP16 modunda çevrim başına iki FP16 işlem tamamlar.
- FMA işlemi iki FLOP olarak sayılır.

Bu varsayımlara göre:

| Model | FP32 teorik tepe | FP32 FMA tepe | FP16 teorik tepe | FP16 FMA tepe |
|---|---:|---:|---:|---:|
| G128 | 16,384 TFLOP/s | 32,768 TFLOP/s | 32,768 TFLOP/s | 65,536 TFLOP/s |
| G256 | 32,768 TFLOP/s | 65,536 TFLOP/s | 65,536 TFLOP/s | 131,072 TFLOP/s |
| G512 | 65,536 TFLOP/s | 131,072 TFLOP/s | 131,072 TFLOP/s | 262,144 TFLOP/s |
| G1024 | 131,072 TFLOP/s | 262,144 TFLOP/s | 262,144 TFLOP/s | 524,288 TFLOP/s |

RTX 5090 için yayımlanan yaklaşık FP32 teorik tepe değeri 104,8 TFLOP/s'dir. Bu sayı, belirli bir yürütme modeline dayalı teorik tepedir; oyun performansıyla doğrudan eşdeğer değildir.

NEXSUS tablosu da gerçek donanım ölçümü değildir. Yürütme aşamalarının bu hızlara ulaşması; komut bağımsızlığına, veri yollarına, zamanlayıcıya ve bellek beslemesine bağlıdır. FP16 için ayrıca operand biçimi, biriktirme türü ve desteklenen işlem başına throughput doğrulanmalıdır.

## 10. Grafik ve ışın izleme kaynakları

NEXSUS GPU, genel hesaplama kaynaklarından ayrı grafik işlevlerine ihtiyaç duyar.

Öngörülen grafik alt sistemi şunları içerir:

- Geometri ve vertex işleme.
- Clipping ve culling.
- Rasterizer.
- Texture Mapping Unit (TMU).
- Render Output Unit (ROP).
- Görüntü sonlandırma ve çıktı yönetimi.
- BVH dolaşımı ve ışın-kesişim hesapları için RTU.

RTU sayısının G128, G256, G512 ve G1024 arasında nasıl ölçekleneceği henüz kesinleştirilmemiştir.

Daha fazla Line bulunması tek başına daha yüksek oyun performansı sağlamaz. Rasterizasyon, texture örnekleme, ROP kapasitesi, geometri akışı ve ışın izleme kaynakları da dengeli olmalıdır.

## 11. Güç ve fiziksel tasarım

RTX 5090'ın 575 W kart gücü, NEXSUS için doğrudan bir güç tahmini olarak kullanılamaz.

NEXSUS modellerinin güç bütçesi şu bileşenler belirlendikten sonra hesaplanmalıdır:

- Yürütme birimlerinin fiziksel alanı ve anahtarlama etkinliği.
- PRAM ve önbelleklerin alanı ve erişim enerjisi.
- Harici bellek arayüzünün enerji tüketimi.
- GPU Fabric bağlantıları ve kuyrukların maliyeti.
- Grafik ve RTU alt sistemleri.
- Saat dağıtımı, gerilim ve üretim süreci.

Özellikle G1024'te çok yüksek kaynak sayısı nedeniyle güç, soğutma ve yonga alanı mimarinin en önemli doğrulama konularındandır.

## 12. Sonuç

NEXSUS GPU'nun ölçeklenebilir yapısı, yüksek paralellik ve esnek hesaplama hedefi üzerine kuruludur. G1024 modeli 8.192 Line, 32 GB veri belleği, 1.024 bit veri yolu ve 128 MiB L2 hedefiyle tasarlanmıştır.

Mevcut teorik hesaplara göre G1024:

- RTX 5090'dan daha geniş bir toplam bellek veri yolu hedefler.
- Belirtilen hız ve %90 varsayımsal verimlilik altında 2.304 GB/s etkin bant genişliği hedefler.
- Çok sayıda FP16/FP32 yürütme aşaması içerir.
- Group Fabric ve bağımsız bellek kaynaklarıyla paralel çalışmayı artırmayı amaçlar.

Ancak bu değerler henüz gerçek performans üstünlüğünü kanıtlamaz. RTX 5090'ı geçme hedefi, simülasyonlar ve daha sonra fiziksel prototip ölçümleriyle doğrulanmalıdır.

## 13. Sonraki doğrulama adımları

1. FP16, FP32, FMA ve karma hassasiyet yürütme davranışlarını kesinleştirmek.
2. Line ve Group düzeyindeki bağımlılık, forwarding ve kaynak çakışmalarını simüle etmek.
3. GPU Fabric'in kanal, banka, kuyruk ve geri basınç davranışlarını test etmek.
4. Bellek erişim örüntülerine göre gerçekçi bant genişliği verimliliğini hesaplamak.
5. Grafik ve RTU alt sistemlerinin kapasitesini tanımlamak.
6. G128–G1024 için alan, güç ve soğutma bütçelerini tahmin etmek.
7. Aynı iş yüklerinde NEXSUS simülasyon sonuçlarını RTX 5090 ölçümleriyle karşılaştırmak.

**Nihai hedef:** Yalnızca daha fazla hesaplama birimi üretmek değil, bu birimleri veri beklemeden ve gereksiz senkronizasyon oluşturmadan mümkün olduğunca paralel çalıştırabilen dengeli bir GPU mimarisi geliştirmektir.
