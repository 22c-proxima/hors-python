from typing import List


class Keywords:

    AFTER             = ['через']
    AFTER_POSTFIX     = ['спустя']
    PREVIOUS_POSTFIX  = ['назад']
    NEXT              = ['следующий', 'будущий']
    PREVIOUS          = ['прошлый', 'прошедший', 'предыдущий']
    CURRENT           = ['этот', 'текущий', 'нынешний']
    CURRENT_NEXT      = ['ближайший', 'грядущий']

    TODAY             = ['сегодня']
    TOMORROW          = ['завтра']
    AFTER_TOMORROW    = ['послезавтра']
    YESTERDAY         = ['вчера']
    BEFORE_YESTERDAY  = ['позавчера']

    HOLIDAY           = ['выходной']

    SECOND            = ['секунда', 'сек']
    MINUTE            = ['минута', 'мин']
    HOUR              = ['час', 'ч']

    DAY               = ['день']
    WEEK              = ['неделя']
    MONTH             = ['месяц', 'мес']
    YEAR              = ['год']

    NOON              = ['полдень']
    MORNING           = ['утро']
    EVENING           = ['вечер']
    NIGHT             = ['ночь']

    HALF              = ['половина', 'пол']
    QUARTER           = ['четверть']

    DAY_IN_MONTH      = ['число']

    JANUARY           = ['январь', 'янв']
    FEBRUARY          = ['февраль', 'фев']
    MARCH             = ['март', 'мар']
    APRIL             = ['апрель', 'апр']
    MAY               = ['май', 'мая']
    JUNE              = ['июнь', 'июн']
    JULY              = ['июль', 'июл']
    AUGUST            = ['август', 'авг']
    SEPTEMBER         = ['сентябрь', 'сен', 'сент']
    OCTOBER           = ['октябрь', 'окт']
    NOVEMBER          = ['ноябрь', 'ноя', 'нояб']
    DECEMBER          = ['декабрь', 'дек']

    MONDAY            = ['понедельник', 'пн']
    TUESDAY           = ['вторник', 'вт']
    WEDNESDAY         = ['среда', 'ср']
    THURSDAY          = ['четверг', 'чт']
    FRIDAY            = ['пятница', 'пт']
    SATURDAY          = ['суббота', 'сб']
    SUNDAY            = ['воскресенье', 'вс']

    DAYTIME_DAY       = ['днём', 'днем']
    TIME_FROM         = ['в', 'с']
    TIME_TO           = ['до', 'по']
    TIME_ON           = ['на']    

    @staticmethod
    def months() -> List[List[str]]:
        return [
            Keywords.JANUARY,
            Keywords.FEBRUARY,
            Keywords.MARCH,
            Keywords.APRIL,
            Keywords.MAY,
            Keywords.JUNE,
            Keywords.JULY,
            Keywords.AUGUST,
            Keywords.SEPTEMBER,
            Keywords.OCTOBER,
            Keywords.NOVEMBER,
            Keywords.DECEMBER
        ]

    @staticmethod
    def days_of_week() -> List[List[str]]:
        return [
            Keywords.MONDAY,
            Keywords.TUESDAY,
            Keywords.WEDNESDAY,
            Keywords.THURSDAY,
            Keywords.FRIDAY,
            Keywords.SATURDAY,
            Keywords.SUNDAY
        ]
