# NEXSUS GPU Architecture
## Line, Group, GPU Fabric ve Grafik Motoru Tasarımı

**Doküman Kodu:** NEXSUS-GPU-ARCH-001  
**Konu:** Ölçeklenebilir GPU hesaplama ve grafik işleme mimarisi  
**Statü:** Kavramsal mimari taslağı — geliştirme aşamasında  
**Tasarım yaklaşımı:** Modüler, dinamik yönlendirmeli, hiyerarşik ve ölçeklenebilir donanım

---

## 1. Amaç ve Tasarım İlkeleri

NEXSUS GPU, genel amaçlı hesaplama ile grafik işleme görevlerini ortak bir hesaplama altyapısı üzerinde birleştirmeyi hedefleyen modüler bir GPU mimarisidir.

Mimari; Line tabanlı işlem birimleri, Group yapıları, yerel PRAM bellekleri, FP16/FP32 çift modlu hesaplama kaynakları, FP64 motorları, Matrix Engine birimleri ve GPU Fabric tarafından yönetilen veri akışından oluşur.

Temel hedefler:

- Hesaplama kaynaklarını gereksiz yere sabit işlem zincirlerine bağlamamak.
- Veri bağımlılığı olduğunda sonuçları doğrudan sonraki işlem birimine aktarabilmek.
- Line ve Group seviyesinde yerel bellek erişimini desteklemek.
- Kontrol trafiği ile veri trafiğini birbirinden ayırmak.
- Grafik, ışın izleme ve genel amaçlı hesaplamayı aynı GPU üzerinde birlikte yürütebilmek.
- GPU kapasitesini 128 Line'dan 1024 Line'a ve gerektiğinde daha ileri seviyelere ölçekleyebilmek.

Bu dokümandaki kapasite ve performans hedefleri kavramsaldır. Gerçek donanım alanı, saat frekansı, güç tüketimi ve performans henüz doğrulanmış değildir.

## 2. Hiyerarşik Mimari

NEXSUS GPU dört temel seviyeden oluşur:

1. Line: Yerel hesaplama kaynakları ve Line PRAM.
2. Group: Sekiz Line'ın, yerel FP64 ve Matrix Engine kaynaklarının ve Group PRAM'in bir araya geldiği yapı.
3. GPU Fabric: Line, Group, grafik motorları ve RTU arasındaki veri akışını ve iş dağıtımını yöneten altyapı.
4. Grafik ve özel işlem motorları: Rasterizer, Texture Unit, ROP ve Ray Tracing Unit gibi belirli görevleri hızlandıran birimler.

Üst seviye Fabric, kaynakların ve işlerin dağıtımını düzenler. Yerel veri aktarımı ise her işlem için merkezî denetleyiciden izin beklemek zorunda kalmayacak şekilde tasarlanır.

## 3. Line Mimarisi

Line, NEXSUS GPU'nun temel hesaplama birimidir.

Her Line için planlanan kaynaklar:

- INT16-A
- INT16-B
- INT32
- Sekiz adet FP16/FP32 çift modlu işlem aşaması
- Line'a özel PRAM
- Yerel veri yönlendirme ve işlem kontrolü

Normal giriş/çıkış tutucu register'ları, operand register'ları ve sonuç register'ları mimarinin mevcut parçaları kabul edilir. Bu register'lar ayrıca birer bellek veya işlem birimi olarak sayılmaz.

### 3.1. FP16/FP32 çift modlu işlem kaynakları

FP16 ve FP32 için tamamen ayrı hesaplama kümeleri kurmak yerine ortak donanım kaynaklarının iki formatta çalışabilmesi hedeflenir.

FP16 modunda uygun bir işlem birimi iki bağımsız 16-bit işlem yolunu çalıştırabilir. FP32 modunda ise tek bir 32-bit kayan nokta işlemi yürütür.

Bu yaklaşımın amaçları:

- FP16 işlemlerinde daha yüksek işlem yoğunluğu sağlamak.
- FP32 gerektiğinde daha yüksek sayısal hassasiyete geçebilmek.
- Ayrı ve büyük FP16/FP32 donanım kümelerinin tekrarlanmasını azaltmak.
- Aynı hesaplama kaynaklarını farklı iş yüklerine uyarlayabilmek.

Bu paylaşımın gerçek alan ve performans avantajı, aritmetik devrelerin ve veri yollarının ayrıntılı tasarımına bağlıdır. FP32 donanımını yalnızca bit genişliğini ikiye bölerek iki FP16 birimine dönüştürmek yeterli değildir; üs, anlamlı basamak, yuvarlama ve özel değer işlemleri de desteklenmelidir.

### 3.2. Dinamik zincirleme

FP işlem aşamaları sürekli birbirine bağlı, sabit bir zincir olarak çalışmak zorunda değildir.

Varsayılan çalışma biçimi bağımsız işlem yürütmedir. Komutlar arasında veri bağımlılığı bulunduğunda ve uygun kaynak hazır olduğunda doğrudan sonuç aktarımı devreye girer.

Bu mekanizma:

- Ara sonuçların gereksiz yere PRAM'e yazılmasını azaltabilir.
- Sonuçların sonraki işlem birimine daha düşük gecikmeyle aktarılmasını sağlayabilir.
- Bağımsız komutların paralel çalışmasına izin verir.
- Veri bağımlılığı bulunan komutların uygun sırada yürütülmesini sağlar.

Dinamik zincirleme, fiziksel olarak sabit bir işlem sırası dayatmak yerine yönlendirme ve bypass ağı üzerinden gerçekleştirilmesi planlanan bir özelliktir.

### 3.3. Line PRAM

Her Line'ın kendisine ait bir PRAM alanı bulunur.

**Fiziksel yerleşim kararı:** Line PRAM, ilgili Line bloğunun içine gömülü olarak yerleştirilir.

Bu yerleşimin amacı:

- Line ile PRAM arasındaki fiziksel mesafeyi azaltmak.
- Yerel erişimi hızlandırmak.
- Group seviyesindeki ortak trafiği azaltmak.
- Line'a özel veri ve ara sonuçların yerel olarak tutulmasını sağlamak.

PRAM kapasitesi ve port sayısı henüz kesinleştirilmemiştir. Daha önce yapılan simülasyonda 1 KiB sayfa, 64 işlemli sentetik iş yükü için test edilen küçük sayfalar arasındaki ilk uygun aday olarak görülmüştür. Bu sonuç yalnızca ilgili adres örüntüsü ve simülasyon varsayımları için geçerlidir; nihai donanım kapasitesi kararı değildir.

## 4. Group Mimarisi

Bir Group, sekiz Line'dan oluşur.

Her Group'ta:

- 8 Line
- 16 FP64 motoru değil, **2 FP64 motoru**
- 2 Matrix Engine
- Group PRAM
- Group Fabric

bulunur.

FP64 ve Matrix Engine sayıları, her dört Line'lık alt yapıda bir FP64 ve bir Matrix Engine bulunması kararından gelir. Dolayısıyla her sekiz Line'lık Group'ta iki alt yapı ve toplam iki FP64 ile iki Matrix Engine yer alır.

### 4.1. Group PRAM

Group PRAM, aynı Group içindeki Line'lar arasında ortak kullanılabilecek yerel veri alanıdır.

**Fiziksel yerleşim kararı:** Group PRAM, kendisini kullanan Group'un çevresine yerleştirilir.

Bu yerleşim, PRAM'i tek bir Line'ın içine gömmek yerine Group içindeki birden fazla Line'ın erişimine uygun hâle getirir.

Group PRAM'in kapasitesi, port sayısı ve bank düzeni henüz belirlenmemiştir. Tasarım aşamasında erişim çakışmaları ve eşzamanlı erişim kapasitesi değerlendirilmelidir.

Line PRAM ve Group PRAM farklı amaçlara hizmet eder:

- Line PRAM: Line'a özgü yerel veri ve ara sonuçlar.
- Group PRAM: Aynı Group içindeki Line'lar arasında paylaşılması gereken veriler.

### 4.2. Group Fabric

Group Fabric, Group içindeki kaynakların ve yerel veri aktarımının yönetiminden sorumludur.

Başlıca görevleri:

- Sekiz Line arasındaki veri yönlendirmesini yönetmek.
- Line PRAM ve Group PRAM erişimlerini düzenlemek.
- FP64 ve Matrix Engine isteklerini uygun kaynaklara yönlendirmek.
- Veri bağımlılıklarını ve kaynak çakışmalarını takip etmek.
- Hazır olan bağımsız işlerin beklemeden ilerlemesini sağlamak.
- Tamamlanan işlemlerin sonuçlarını ilgili kaynaklara aktarmak.

Group Fabric'in her aktarımı tek tek merkezî bir denetleyiciden geçirmesi hedeflenmez. Yerel ve sık kullanılan aktarım yolları mümkün olduğunca doğrudan çalışmalıdır.

## 5. GPU Fabric

GPU Fabric, GPU'nun genel iş dağıtımını, kaynak koordinasyonunu ve veri akışını yönetir.

Bu birim yalnızca fiziksel bir veri yolu değildir. Kontrol mantığı, zamanlama, yönlendirme ve trafik yönetimini bir arada içeren bir altyapıdır.

### 5.1. Control Fabric

Control Fabric şu bilgileri yönetir:

- Komut ve iş kuyruğu durumu.
- Kaynak tahsisi ve öncelikler.
- Veri bağımlılıkları.
- İşlem tamamlanma bildirimleri.
- Kaynakların uygunluk durumu.
- Gerektiğinde geri basınç ve yeniden zamanlama.

### 5.2. Data Fabric

Data Fabric, hesaplama sırasında oluşan asıl veri trafiğini taşır.

Öncelikli görevleri:

- Line'lar arasındaki sonuç aktarımı.
- Line ve Group PRAM erişimleri.
- Group'lar arasındaki veri aktarımı.
- RTU, grafik motorları ve hesaplama kaynakları arasındaki veri hareketi.
- Grafik hattının aşamaları arasındaki aktarım.

Kontrol trafiği ile veri trafiğinin ayrılması, sık veri aktarımının merkezî kontrol mantığı tarafından gereksiz yere yavaşlatılmasını önlemeyi amaçlar.

### 5.3. Hiyerarşik yönlendirme

GPU büyüdükçe bütün Line'ları tek bir devasa çapraz bağlantı ağına bağlamak yerine hiyerarşik bir yapı kullanılması planlanır:

- Line içi yönlendirme.
- Group Fabric.
- Gerektiğinde bölgesel GPU Fabric.
- Üst seviye GPU Fabric Controller.

G128 gibi daha küçük modellerde bölgesel katman gerekmeyebilir. G512 ve G1024 gibi büyük modellerde ise bölgesel yönlendirme, merkezî kontrol yükünü azaltmak için değerlendirilecektir.

## 6. Grafik Motoru

Grafik motoru, Line havuzunun yerine geçen bir yapı değildir. Line'larla birlikte çalışan özel işlevli donanım katmanıdır.

Programlanabilir gölgelendirme ve hesaplama işleri Line havuzunda yürütülürken, belirli grafik görevleri özel motorlar tarafından hızlandırılır.

### 6.1. Komut ve iş yükü yöneticisi

Çizim komutlarını alır, iş yüklerini belirler ve uygun grafik veya hesaplama kaynaklarına dağıtır.

### 6.2. Geometri motoru

Vertex işleme, geometri hazırlığı, clipping ve culling gibi aşamaları yürütür.

Bazı işlemler özel donanımla hızlandırılırken daha esnek hesaplamalar Line havuzunda gerçekleştirilebilir.

### 6.3. Rasterizer

Üçgenleri ekran üzerindeki piksel ve örnek konumlarına dönüştürür.

Rasterizer kapasitesi yalnızca Line sayısına göre belirlenemez. Üçgen işleme hızı, örnek sayısı, çözünürlük ve sahne karmaşıklığı birlikte değerlendirilmelidir.

### 6.4. Texture Unit

Doku örnekleme, adresleme ve filtreleme gibi işlemleri hızlandırır.

Texture Unit'lerin kapasitesi, özellikle yüksek çözünürlüklü ve çok sayıda doku erişimi gerektiren sahnelerde ayrı bir performans ölçütüdür.

### 6.5. ROP / Pixel Output

Depth ve stencil testleri, blending ve son piksel değerlerinin hedef görüntü alanına yazılması gibi görevleri üstlenir.

Line sayısının artırılması, ROP kapasitesi yetersizse piksel çıktı hızını tek başına artırmaz.

### 6.6. Görüntü birleştirme ve ekran çıkışı

Grafik hattının tamamlanan görüntüsü son aşamada birleştirilir ve ekran çıkışına hazırlanır. Görüntü ölçekleme, anti-aliasing ve diğer görüntü işleme özelliklerinin hangi motorlarda gerçekleştirileceği ayrıca tanımlanacaktır.

## 7. Ray Tracing Unit (RTU)

Işın izleme, yoğun ve farklı karakterde iş yükleri oluşturduğu için ayrı hızlandırıcı donanım kullanılması planlanır.

RTU'nun temel görevleri:

1. BVH ağacında gezinme.
2. Işın-kutu kesişim testleri.
3. Işın-üçgen kesişim testleri.
4. Sonuçların ilgili Line'lara aktarılması.
5. Bekleyen ışınların ve tamamlanmamış işlerin yönetimine destek verilmesi.

Işının oluşturulması, bulunan yüzeyin gölgelendirilmesi ve materyal hesaplamaları genel hesaplama kaynaklarında yürütülebilir. RTU, bu işlerin tamamını üstlenmek yerine pahalı ve tekrarlanan kesişim işlemlerini hızlandırır.

RTU ile Line havuzu arasında GPU Fabric üzerinden iş ve veri koordinasyonu sağlanır. Bir RTU sonucu beklenirken ilgisiz işlerin çalışmaya devam edebilmesi hedeflenir.

## 8. GPU Ürün Ailesi

İlk ürün ailesi, her Group'ta sekiz Line olacak şekilde ölçeklendirilir.

| Model | Group | Toplam Line | FP64 motoru | Matrix Engine |
|---|---:|---:|---:|---:|
| G128 | 16 | 128 | 32 | 32 |
| G256 | 32 | 256 | 64 | 64 |
| G512 | 64 | 512 | 128 | 128 |
| G1024 | 128 | 1024 | 256 | 256 |

FP16/FP32 işlem aşaması sayısı, her Line için sekiz çift modlu aşama varsayımıyla sırasıyla 1024, 2048, 4096 ve 8192 olur.

Bu sayılar mimari kaynak sayılarıdır; gerçek işlem verimi, komut düzeni, işlem gecikmesi, kaynak paylaşımı ve saat frekansı ile birlikte değerlendirilmelidir.

G128, G256, G512 ve G1024 isimleri öncelikle kaynak ölçeğini ifade eder. Bunların 2K, 4K veya 8K çözünürlükte belirli FPS değerlerini sağlayacağı henüz doğrulanmış değildir.

## 9. Ölçekleme ve Grafik Performansı

GPU kapasitesi büyüdükçe yalnızca Line sayısının artırılması yeterli değildir.

Aşağıdaki kaynaklar da dengeli biçimde ölçeklenmelidir:

- Geometri ve rasterizasyon kapasitesi.
- Texture Unit sayısı ve örnekleme hızı.
- ROP kapasitesi.
- RTU sayısı ve ışın işleme hızı.
- GPU Fabric bant genişliği ve eşzamanlı aktarım kapasitesi.
- PRAM kapasitesi, port sayısı ve bank düzeni.
- Görüntü işleme ve denoising kapasitesi.

İlk RTU ölçekleme hipotezi G128, G256, G512 ve G1024 için sırasıyla 2, 4, 8 ve 16 RTU bloğudur. Bu sayıların doğrulanması için RTU başına işlem kapasitesi, ortalama BVH adım sayısı ve hedef iş yükleri üzerinden değerlendirme yapılmalıdır.

Çözünürlük tek başına performans ölçütü değildir. 8K çözünürlükte piksel sayısı 4K'nın dört katıdır; ancak ışın izleme, materyal karmaşıklığı ve görüntü kalitesi ayarları toplam hesaplama yükünü daha da değiştirebilir.

## 10. Bellek ve Register Varsayımları

Bu mimari dokümanda giriş/çıkış tutucu register'ları, operand register'ları ve normal işlem register'ları mevcut kabul edilir.

Register sayıları, register dosyasının fiziksel yerleşimi ve bu register'ların alan maliyeti bu aşamada ayrıca modellenmemektedir.

Line PRAM ve Group PRAM ise açık mimari bileşenleridir ve fiziksel yerleşimleri tanımlanmıştır.

Belleklerin yeterli kapasite ve hızda olduğu varsayımı mimari tartışmada kullanılabilir; ancak gerçek donanım değerlendirmesinde bellek bant genişliği, erişim gecikmesi, bank çakışmaları, port sayısı ve fiziksel alan ayrıca ölçülmelidir.

## 11. Geliştirme Sırası

Önerilen geliştirme aşamaları:

1. Line içindeki işlem birimlerinin ve dinamik zincirleme mekanizmasının tanımlanması.
2. Line PRAM kapasitesi ve erişim modelinin belirlenmesi.
3. Group PRAM ve Group Fabric bağlantılarının tasarlanması.
4. Control Fabric ve Data Fabric protokollerinin belirlenmesi.
5. Grafik motoru bileşenlerinin kapasite hedeflerinin tanımlanması.
6. RTU alt birimlerinin ve ışın kuyruğu yönetiminin tasarlanması.
7. G128–G1024 ölçekleme modellerinin oluşturulması.
8. Sentetik iş yükleri ve grafik iş yükleriyle simülasyon.
9. Alan, güç, gecikme ve bant genişliği tahminleri.
10. Tasarım kararlarının doğrulama sonuçlarına göre güncellenmesi.

## 12. Sonuç

NEXSUS GPU mimarisinin temel yaklaşımı, yüksek sayıda programlanabilir Line'ı özel grafik ve ışın izleme motorlarıyla birleştirmek ve bunların veri akışını hiyerarşik GPU Fabric üzerinden yönetmektir.

Line PRAM'in Line bloğuna gömülmesi, Group PRAM'in ilgili Group çevresine yerleştirilmesi ve bu kaynakların Group Fabric tarafından yönetilmesi mimarinin temel yerleşim kararlarıdır.

Dinamik zincirleme, bağımsız işlem yürütmeyi varsayılan tutarak yalnızca gerektiğinde doğrudan sonuç aktarımını etkinleştirmeyi amaçlar. FP16/FP32 çift modlu işlem kaynakları ise farklı hassasiyet ve veri genişliği gereksinimlerine aynı altyapı üzerinde yanıt vermeyi hedefler.

GPU Fabric, hesaplama birimleriyle grafik motorları arasındaki iş ve veri hareketini koordine ederek ölçeklenebilirliğin temel bileşeni olacaktır.

Bu mimari şu an bir tasarım çerçevesidir. Performans üstünlüğü, fiziksel alan, güç tüketimi veya belirli bir çözünürlükte FPS hedefi hakkında kesin sonuçlara ulaşmak için ayrıntılı mikro mimari, simülasyon ve doğrulama çalışmaları gereklidir.
