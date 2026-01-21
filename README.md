admin: admin@gmail.com 
amdin_parol: 123



o'zim yaratgan userim: udavlatboyev2@gmail.com
parol: 123


2-3 ta user yana dataga qo'shtirib qo'ydim

python manage.py shell -c "
from configapp.models import Currency;
Currency.objects.get_or_create(code='UZS', defaults={'rate': 1});
Currency.objects.get_or_create(code='USD', defaults={'rate': 12800});
Currency.objects.get_or_create(code='RUB', defaults={'rate': 140});
print('qoshildi!')
"