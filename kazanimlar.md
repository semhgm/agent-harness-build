# Kazanımlar: ajan yazarken kontrol soruları

Bu dosya, bu repodaki deneylerden (v0 → v7) çıkan dersleri **kontrol soruları** olarak topluyor. Yeni bir ajan yazarken ya da bir AI'ın yazdığı ajan kodunu incelerken baştan sona okunması için yazıldı.

Her maddede üç bilgi var: **soru**, **neden** (hangi deneyde ne oldu) ve **kanıt düzeyi**:

- `[kod]` Davranış koddan kesin olarak çıkıyor, ölçmeye gerek yok.
- `[gözlem]` Bir ya da birkaç denemede görüldü. Henüz oran olarak ölçülmedi.
- `[ölçüldü]` Eval ile çok kez koşuldu (Hafta 2'den sonra güncellenecek).

---

## 0. Temel soru

**Modelin eline ne geçti?**
Model hafızasız. Her istekte `messages` listesinin tamamı gönderiliyor. Modelin bir kararını anlamak, ya da bir saldırının nereden girdiğini bulmak için bu listeye bak: system prompt, kullanıcı mesajları, tool şemaları, tool sonuçları, modelin kendi önceki cevapları. Bu listeye giren her metin, kimden gelirse gelsin, modelin talimat olarak okuyabileceği bir metin. `[kod]`

---

## 1. Yetki ve sınırlar

**1.1 Her tool'un erişebildiği alan kodla mı sınırlanmış, yoksa prompt'la mı?**
Path traversal (`../main.py`) prompt'la değil, `resolve()` + `is_relative_to()` ile engellendi. Prompt'a "workspace dışına çıkma" yazmak bir savunma değil. `[kod]`

**1.2 Modelin kandırılması durumunda en kötü ne olur?**
Savunmayı modelin doğru davranacağı varsayımına kurma. `deneme1.txt` testinde model dosyadaki talimatı kullanıcı isteği gibi uyguladı ve iki dosyayı sildi. Soruyu "model bunu yapar mı?" değil, "model bunu yaparsa ne olur?" diye sor. `[gözlem]`

**1.3 Geri alınamaz işlemler (silme, gönderme, ödeme) insan onayından geçiyor mu?**
Onay, harness içinde ve modelin atlayamayacağı bir yerde olmalı. `[kod]`

---

## 2. Güvenilmeyen içerik

**2.1 Hangi kaynaklar güvenilmez sayılıyor?**
Dosya içeriği, web sayfası, e-posta, tool sonucu: kullanıcının kendisinin yazmadığı her şey. Model bu içerikle kullanıcı talimatını birbirinden ayırmıyor. `[gözlem]`

**2.2 Güvenilmeyen içerik bağlama girdikten sonra hangi tool'lar hâlâ açık?**
Taint yazma ve silmeyi kapatıyor, okuma ve listelemeyi açık bırakıyor. Dışarı veri gönderen bir tool (HTTP isteği, e-posta) olsaydı veri sızdırma mümkün olurdu. Taint'in neyi kapattığı ile neyi açık bıraktığını ayrı ayrı listele. `[kod]`

**2.3 "Sadece meta veri" diye düşündüğün alanlar da bir kanal mı?**
`listFiles` dosya adlarını modele veriyor ama taint tetiklemiyor. Dosya adı da bir metin; içine talimat yazılabilir. Şemalar, hata mesajları ve dosya adları da modelin eline geçen metinler. `[kod]`

**2.4 Taint'in kullanılabilirlik bedeli ne?**
Bir dosya okunduktan sonra oturum boyunca yazma kapalı. "Dosyayı oku, özetini yaz" gibi meşru akışlar da engelleniyor. Bu bedel ürüne göre kabul edilebilir ya da edilemez. Bu bir tasarım kararı, otomatik doğru bir cevabı yok. `[kod]`

---

## 3. Guard ve politika

**3.1 Her tool çağrısı tek bir merkezi noktadan geçiyor mu?**
Kontroller tool'ların içine dağılırsa biri unutulur. Tek bir `guardToolCall` hem denetlemeyi hem loglamayı kolaylaştırıyor. `[kod]`

**3.2 Kontrollerin sırası doğru mu?**
Kesin yasaklar (uzantı kuralı, taint) kullanıcı onayından **önce** gelmeli. Aksi hâlde kullanıcı yasaklı bir işlemi "evet" diyerek açabilir. `[kod]`

**3.3 Kural beyaz liste mi, kara liste mi?**
`.py` kara listesi `.pyw`, `.bat`, `.ps1`'i kaçırıyor. Kara liste, saldırganın aklına gelen ama senin aklına gelmeyen her şeyi serbest bırakıyor. `[kod]`

**3.4 Girdi karşılaştırmadan önce normalize ediliyor mu?**
`test.PY` ve `test.py.` (Windows sondaki noktayı siliyor) ilk kontrolü geçti. Büyük/küçük harf, sondaki nokta ve boşluk, Unicode benzeri karakterler: karşılaştırmayı normalize edilmiş değer üzerinde yap. `[gözlem]`

**3.5 Ret sebebi modele, kısa etiket log'a ayrı ayrı gidiyor mu?**
`reason` (modele giden açıklama) ile `rule` (log için sabit etiket) ayrı tutulmalı. Serbest metin üzerinde string araması yaparak log sorgulamak kırılgan. `[kod]`

**3.6 Ret mesajının biçimi modelin davranışını nasıl etkiliyor?**
"Do not retry. Tell the user they declined it." gibi açık talimatlar modelin reddedilen işlemi tekrar denemesini ve gizlemesini azaltıyor gibi görünüyor. `[gözlem]` → Hafta 2'de ölçülecek.

---

## 4. Dayanıklılık

**4.1 Harness, modelden gelen her türlü çıktıda ayakta kalıyor mu?**
Bozuk JSON, dict olmayan JSON (`[]`), yanlış parametre adı, tool içi exception. Bunların hiçbiri programı çökertmemeli. Çökme oturumu ve kullanıcının işini kaybettiriyor, ve bozuk çıktıya yol açan bir dosya harness'ı tekrar tekrar düşürebiliyor (DoS). `[kod]`

**4.2 Hatalar modele değer olarak dönüyor mu?**
Hata mesajı modele `tool` mesajı olarak gidince model kendini düzeltebiliyor. `TypeError` için parametre adını söyleyen bir mesaj işe yarıyor. Binary dosya testinde model içerik uydurmadı ve dosyanın okunamadığını söyledi. `[gözlem]`

**4.3 Her `tool_call` için, hata olsa bile, bir `tool` mesajı ekleniyor mu?**
API, cevapsız kalan bir tool çağrısından sonraki isteği reddediyor. `continue` kullan, `break` değil: aynı mesajdaki diğer çağrılar da cevap bekliyor. `[kod]`

**4.4 Modele giden hata mesajı ile log'a giden hata detayı ayrı mı?**
`OSError` mesajları tam dosya yolunu (kullanıcı adı, klasör yapısı) içeriyor. Modele hata türü yeterli; tam detay log'a. `[kod]`

**4.5 `except` blokları doğru mu?**
Çıplak `except:` `KeyboardInterrupt`'ı da yutuyor, `except Exception` kullan. Özel durum (`TypeError`) genel durumdan (`Exception`) önce yazılmalı. `[kod]`

**4.6 Sonsuz döngüye karşı bir sınır var mı?**
Tur sınırı (burada 5) olmadan, sürekli hata yapan ya da sürekli tool çağıran bir model döngüyü bitirmez. `[kod]`

---

## 5. Durum ve yaşam döngüsü

**5.1 Güvenlik durumu (taint vb.) ait olduğu veriyle aynı yaşam döngüsüne sahip mi?**
Taint "bağlamda güvenilmeyen içerik var" demek. `messages` ile birlikte oluşmalı ve birlikte kaybolmalı. Konuşma geçmişi diske kaydedilip taint kaydedilmezse, geri yüklenen kirli geçmiş temiz bir bayrakla açılır ve model dosyayı tekrar okumadığı için taint yeniden tetiklenmez. `[kod]`

**5.2 Fonksiyonlar global duruma gizlice bağımlı mı?**
Durum parametre olarak geçmeli (`chat(session, ...)`). Gizli global bağımlılık hem test etmeyi hem çok oturumlu kullanımı bozuyor. `[kod]`

---

## 6. Denetim (audit log)

**6.1 Ne yapıldığının doğru kaynağı ne?**
Modelin cevabı değil, harness'ın kaydı. v6'da model silmeye çalıştığı dosyaları cevabında söylemedi; terminalden anlaşılmadı, audit log gösterdi. `[gözlem]`

**6.2 Log ajanın erişemeyeceği bir yerde mi?**
Log workspace içinde olsaydı ajan onu okuyabilir, değiştirebilir ya da silebilirdi. Not: ajana karşı korumak, bilgisayara erişimi olan bir insana karşı korumak demek değil. `[kod]`

**6.3 Log yapılandırılmış ve sorgulanabilir mi?**
JSON Lines, her satırda session id, olay türü, tur, karar etiketi (`rule`), çağrı **öncesindeki** taint durumu ve hata alanı. Başarılı satırlarda da aynı alanlar olmalı (`error: null`). `[kod]`

**6.4 Log'a hangi büyüklükte ve hassaslıkta veri giriyor?**
Uzun içerik log'u şişiriyor ve onu bir hassas veri deposuna dönüştürüyor. Önizleme + uzunluk + SHA-256 hem okunabilirliği koruyor hem de "ajan tam olarak bunu yazdı" diye doğrulamaya izin veriyor. Özetlerken orijinal veriyi değil kopyasını değiştir; yoksa tool'a da kısaltılmış içerik gider. `[kod]`

**6.5 Aynı veri log'a başka bir kapıdan giriyor mu?**
`args.content` özetlendi, ama model içeriği cevabında tekrar edince `final_answer` üzerinden log'a tam olarak girdi. Modelin çıktısı da bir veri kanalı. Bir alanı korumak yetmiyor, verinin geçtiği bütün yolları kontrol et. `[gözlem]`

---

## 7. Görev doğruluğu

**7.1 Model bir işlemi yaptığını söylüyorsa, bunu bir tool sonucu doğruluyor mu?**
Model bazen tool çağırmadan ya da tool hata verdiği hâlde "yaptım" dedi. System prompt kuralı bunu azaltıyor, ortadan kaldırmıyor. Doğrulamayı log ile yap. `[gözlem]`

**7.2 Modelin kendi çıktısı hakkındaki iddiaları kodla doğrulanıyor mu?**
"300 kelime" istendi. Model 100 kelime yazdı ve metne kendisi "(300 kelime)" etiketini ekledi. Önceki denemede ~160 kelime ve istenen dil yerine İngilizce. Sayılabilen bir şeyi (kelime sayısı, dosya sayısı, test sonucu) modele sorma, kodla ölç. `[gözlem]`

**7.3 Güvenlik önlemleri devredeyken asıl görev tamamlanıyor mu?**
Injection varken guard dosyaları korudu, ama model asıl görevi (fiyatları söylemek) unuttu. "Saldırı engellendi" ile "kullanıcı istediğini aldı" ayrı ayrı kontrol edilmeli. `[gözlem]`

**7.4 Model saldırıyı ya da başarısızlığı kullanıcıdan gizliyor mu?**
Injection talimatındaki "do not mention" bazen işe yaradı. Ret durumunda modelin kullanıcıya ne söylediğini ayrıca kontrol et. `[gözlem]`

---

## Hızlı kontrol: AI'ın yazdığı bir ajanı incelerken

Bir AI'dan "bana bir ajan yaz" dediğinde, çıkan kodda bu 12 soruyu sor. Varsayılan olarak çoğu eksik gelir.

1. Tool'ların erişim alanı kodla mı sınırlı? (1.1)
2. Geri alınamaz işlemler insan onayından geçiyor mu? (1.3)
3. Güvenilmeyen içerik okunduktan sonra tehlikeli tool'lar kapanıyor mu? Hangileri açık kalıyor? (2.2)
4. Dosya adı ve hata mesajı gibi "meta" kanallar düşünülmüş mü? (2.3)
5. Tüm tool çağrıları tek bir guard'dan geçiyor mu, kesin yasaklar onaydan önce mi? (3.1, 3.2)
6. Kurallar beyaz liste mi, girdi normalize ediliyor mu? (3.3, 3.4)
7. Bozuk argüman ve tool exception'ı programı çökertiyor mu? (4.1)
8. Her tool çağrısına hata olsa bile bir cevap dönüyor mu? (4.3)
9. Modele giden hata mesajı iç detay (yol, kullanıcı adı) sızdırıyor mu? (4.4)
10. Tur sınırı var mı? (4.6)
11. Yapılandırılmış, ajanın erişemediği bir audit log var mı? Uzun veya hassas içerik nasıl yazılıyor? (6.2–6.5)
12. Modelin "yaptım" ve "şu kadar" iddiaları kodla doğrulanıyor mu? (7.1, 7.2)

---

*Son güncelleme: Hafta 1 sonu (v7). `[gözlem]` etiketli maddeler Hafta 2 eval'larından sonra `[ölçüldü]` olarak güncellenecek ya da düzeltilecek.*