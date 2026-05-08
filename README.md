Bu araç, Linux (özellikle Arch Linux tabanlı dağıtımlar) üzerinde Discord'a uygulanan erişim engellerini ve Deep Packet Inspection (DPI) kısıtlamalarını aşmak için geliştirilmiş Python tabanlı bir GUI (Arayüz) uygulamasıdır.
✨ Öne Çıkan Özellikler

    Çift Yöntemli Koruma: Hem SpoofDPI (paket manipülasyonu) hem de Cloudflare WARP (VPN tüneli) desteği.

    Otomatik Bağımlılık Kontrolü: Çalıştığı sistemde tk, curl, psmisc gibi paketlerin eksikliğini kontrol eder ve otomatik kurar.

    Akıllı Patch Mekanizması:

        Discord'un settings.json dosyasını güncelleyerek "Host Update" hatalarını engeller.

        .desktop dosyalarını otomatik yamalayarak Discord'un doğrudan proxy ile başlamasını sağlar.

    Gelişmiş Bypass: CAP_NET_RAW yetkisi ile paket bölme (splitting) ve karıştırma (disorder) gibi ileri seviye DPI bypass tekniklerini uygular.

    Entegre Test Aracı: Discord bağlantısının durumunu doğrudan arayüz üzerinden test edebilir.

🛠 Teknik Detaylar

Uygulama iki farklı strateji sunar:

    SpoofDPI (DPI Bypass):

        Trafiği şifrelemek yerine HTTPS paketlerini parçalayarak ISP'nin (İnternet Servis Sağlayıcı) içeriği okumasını engeller.

        Hız kaybı yaşatmaz, IP adresinizi değiştirmez.

        Systemd servis dosyası oluşturarak arka planda stabil çalışmasını sağlar.

    Cloudflare WARP (VPN Tüneli):

        Bağlantıyı Cloudflare ağı üzerinden tüneller.

        Daha güvenilir bir erişim sağlar.

        AUR üzerinden cloudflare-warp-bin paketini otomatik tespit eder veya kurulumunu başlatır.

🚀 Kurulum ve Çalıştırma

Not: Bu araç Arch Linux tabanlı sistemler için optimize edilmiştir. paru veya yay gibi bir AUR yardımcısının yüklü olması önerilir.

    Depoyu klonlayın:
    Bash

    git clone https://github.com/kullaniciadi/discord-bypass.git
    cd discord-bypass

    Scripti çalıştırın:
    Bash

    python3 main.py

🖥 Kullanım Rehberi

    Bağımlılıklar: Script ilk açılışta gerekli sistem paketlerini kontrol eder. Eğer eksik varsa pkexec (GUI şifre ekranı) ile izin isteyerek kurulumu yapar.

    SpoofDPI: "Aktifleştir" butonuna bastığınızda binary indirilir, servis ayarlanır ve Discord kısayolları proxy ayarlarıyla güncellenir.

    WARP: Eğer SpoofDPI ISP engeline takılıyorsa, WARP bölümünden bağlantı kurarak tam tünel moduna geçebilirsiniz.

    Temizleme: "Tümünü Temizle" butonu ile yapılan tüm sistem değişikliklerini, servisleri ve oluşturulan proxy kısayollarını geri alabilirsiniz.

⚠️ Gereksinimler

    Python 3.x

    Arch Linux (veya pacman kullanan bir dağıtım)

    Sudo/Polkit yetkisi (Servis kurulumu ve paket yönetimi için)

⚖️ Lisans

Bu proje eğitim ve kişisel kullanım amacıyla geliştirilmiştir. Kullanım sorumluluğu kullanıcıya aittir.
Önemli Geliştirmeler (Versiyon 2.0 İle Gelenler):

    Multi-threading: Arayüzün donmasını engellemek için tüm işlemler arka plan thread'lerinde çalıştırıldı.

    Otomatik Yetkilendirme: setcap komutu ile spoofdpi binary'sine root yetkisi olmadan raw socket kullanma yetkisi eklendi.

    Kapsamlı Loglama: Hata tespiti için journalctl üzerinden servis logları arayüze entegre edildi.

Bu açıklama, kodunun ne kadar sofistike olduğunu ve sadece bir proxy açıp kapatmaktan çok, sistem düzeyinde entegrasyon (Systemd, Desktop Files, JSON Config) yaptığını güzelce vurgulayacaktır. Başka bir detay eklememi ister misin?
