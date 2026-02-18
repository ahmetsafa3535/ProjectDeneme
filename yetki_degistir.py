import sqlite3

# --- AYARLAR ---
hedef_email = "ahmetsafaatc@gmail.com"  # Yetkisini değiştireceğimiz mail
yeni_yetki = "user"                     # 'admin' veya 'user' yazabilirsiniz

# --- İŞLEM ---
try:
    baglanti = sqlite3.connect("users.db")
    imlec = baglanti.cursor()

    # Güncelleme komutu
    imlec.execute("UPDATE users SET role=? WHERE email=?", (yeni_yetki, hedef_email))
    baglanti.commit()

    if imlec.rowcount > 0:
        print(f"\n✅ BAŞARILI! {hedef_email} hesabı artık -> {yeni_yetki.upper()} yetkisine sahip.")
    else:
        print(f"\n❌ HATA: {hedef_email} diye biri veritabanında bulunamadı.")

    baglanti.close()

except Exception as e:
    print(f"Bir hata oluştu: {e}")