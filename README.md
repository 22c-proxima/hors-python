# Hors
[![MIT License](https://img.shields.io/pypi/l/aiogram.svg?style=flat-square)](https://opensource.org/licenses/MIT)

**hors** - это модуль python для распознавания даты и времени в естественной речи на русском языке. Умеет понимать сложные 
конструкции с абсолютными и относительными датой и временем. В том числе временные периоды. [Хорс](https://ru.wikipedia.org/wiki/%D0%A5%D0%BE%D1%80%D1%81) — это славянский бог солнца

> Оригинальная версия библиотеки написана Денисом Пешехоновым на C# и доступна на [github](https://github.com/DenisNP/Hors) под лицензией MIT. Изменения логики минимальны

## Установка
```bash
pip install hors
```

## Использование
```python
>>> import hors
>>> r = hors.process_phrase('Утром 3 сентября 2059 года мы слушали Шуфутинского')
>>> r.dates[0].type
<DateTimeTokenType.FIXED: 1>
>>> r.dates[0].date_from
datetime.datetime(2059, 9, 3, 9, 0)
>>> r = hors.process_phrase('Полёт Гагарина длился с 9 утра 12 апреля 1961 года до 11 утра')
>>> r.dates[0].type
<DateTimeTokenType.PERIOD: 2>
>>> r.dates[0].date_from
datetime.datetime(1961, 4, 12, 9, 0)
>>> r.dates[0].date_to  
datetime.datetime(1961, 4, 12, 11, 0)
```

## Тестирование
```bash
python -m unittest discover tests
```
