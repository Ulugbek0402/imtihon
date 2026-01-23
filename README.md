Sizning loyihangiz tarixini, texnik muammolarni va UI dizaynini (Inter shrifti, zamonaviy ko'k rangli Dashboard) inobatga olgan holda, professional va to'liq **README.md** faylini tayyorladim.

Ushbu matnni loyihangizning ildiz papkasidagi `README.md` fayliga nusxalab oling:

---

# 🚀 FinanceHome - Smart Wealth Manager

**FinanceHome** — bu shaxsiy moliya va boylikni boshqarish uchun mo'ljallangan zamonaviy Django platformasi. Platforma foydalanuvchilarga o'z daromad va xarajatlarini kuzatish, budjetlar belgilash, maqsadlar (goals) sari intilish va turli valyutalarda o'z mablag'larini tahlil qilish imkonini beradi.

## ✨ Xususiyatlari

* 📊 **Smart Dashboard:** Chart.js yordamida dinamik sarf-xarajatlar tahlili.
* 🌍 **Ko'p tillilik (i18n):** O'zbek, Rus va Ingliz tillarini to'liq qo'llab-quvvatlash.
* 💱 **Multi-Currency:** Turli valyutalarda hisoblar yuritish va kurslarni (rate) boshqarish.
* 🎯 **Budget & Goals:** Oylik budjet cheklovlari va jamg'arma maqsadlarini kuzatib borish.
* 🔐 **Xavfsiz Auth:** Parollarni yangilash va xavfsiz logout tizimi.

---

## 🛠 O'rnatish va Sozlash

### 1. Loyihani klonlash

```bash
git clone https://github.com/Ulugbek0402/imtihon.git
cd imtihon

```

### 2. Virtual muhitni yaratish va ishga tushirish

```bash
python -m venv .venv
.venv\Scripts\activate

```

### 3. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt

```
```bash
python manage.py makemigrations; python manage.py migrate

```
```bash
python manage.py createsuperuser
```
* email == email


---
```bash
python manage.py shell 
```
from configapp.models import Currency

Currency.objects.update_or_create(code='UZS', defaults={'name':'Uzbek soʻm','symbol':'soʻm','rate':1});
Currency.objects.update_or_create(code='USD', defaults={'name':'US Dollar','symbol':'$','rate':12800});
Currency.objects.update_or_create(code='EUR', defaults={'name':'Russian Ruble','symbol':'₽','rate':140});
---

## 🚀 Loyihani ishga tushirish

```bash
python manage.py runserver

```

Endi brauzerda `http://127.0.0.1:8000/` manziliga kiring.

---

## 📁 Loyiha tuzilishi (Key Files)

* `config/urls.py` - Asosiy marshrutlar va i18n sozlamalari.
* `configapp/views.py` - Dashboard mantig'i va tranzaksiyalar hisob-kitobi.
* `templates/home.html` - Dashboard dizayni (Inter font, Chart.js).
* `templates/login.html` - Ko'p tilli login sahifasi.
* `locale/` - Tarjima fayllari (`uz`, `ru`, `en`).

---

