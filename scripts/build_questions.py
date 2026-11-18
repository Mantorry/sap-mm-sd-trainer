import json, re, random, sys
from collections import Counter
from pathlib import Path
from source_facts import MM, SD, parse
ROOT=Path(__file__).resolve().parents[1]
R=random.Random(304719)
GLOSS={'Sales Area':'рынок сбыта','Sales Office':'отдел сбыта','Sales Group':'группа сбыта','Sales Organization':'сбытовая организация','Distribution Channel':'канал сбыта','Sales Order Item':'позиция заказа клиента','Sales Order':'заказ клиента','Purchase Order':'заказ на поставку','Purchase Requisition':'заявка на закупку','Purchasing Info Record':'инфо-запись закупки','Purchasing Organization':'закупочная организация','Purchasing Group':'группа закупок','Company Code':'балансовая единица','Account Assignment Category':'категория контировки','Cost Center':'место возникновения затрат','Internal Order':'внутренний заказ','Valuation Area':'область оценки','Valuation Class':'класс оценки','Material Master':'основная запись материала','Material View':'ракурс материала','Material Type':'вид материала','Supplier Master':'основная запись поставщика','Goods Receipt':'поступление материала','Goods Issue':'отпуск материала','Post Goods Issue':'проводка отпуска материала','PGI':'проводка отпуска материала','Movement Type':'вид движения','Storage Location':'склад','Plant':'завод','Client':'мандант','Shipping Point':'пункт отгрузки','Shipping Conditions':'условия отгрузки','Loading Group':'группа погрузки','Transportation Group':'группа транспортировки','Ship-to Party':'получатель материала','Sold-to Party':'заказчик','Bill-to Party':'получатель счета','Payer':'плательщик','Schedule Line Category':'категория строки графика','Schedule Line':'строка графика','Item Category':'категория позиции','Delivery Split':'разделение поставок','Invoice Split':'разделение фактур','Outbound Delivery':'исходящая поставка','Returns Delivery':'поставка возврата','Returns Order':'заказ на возврат','Billing Document':'документ фактуры','Billing Type':'вид фактуры','Billing Block':'блокировка фактуры','Credit Memo Request':'запрос кредитования','Debit Memo Request':'запрос дебетования','Credit Memo':'кредитовое авизо','Debit Memo':'дебетовое авизо','Copy Control':'контроль копирования','Pricing Analysis':'анализ расчета цены','Pricing Procedure':'схема калькуляции','Pricing Type':'тип расчета цены','Condition Type':'вид условия','Condition Record':'запись условия','Condition Table':'таблица условий','Access Sequence':'последовательность доступа','Condition Update':'обновление условий','Condition Exclusion':'исключение условий','Group Condition':'групповое условие','Rebate Agreement':'соглашение о бонусе','Rebate Accruals':'резервные отчисления по бонусу','Rebate Settlement':'расчет бонуса','Settlement Material':'материал расчета бонуса','Release Status':'статус деблокирования','Processing Status':'статус обработки','Payment Terms':'условия платежа','Net Value':'стоимость нетто','Free Goods':'натуральный рабат','Material Pricing Group':'группа расчета цены материала','Available-to-Promise':'доступное для подтверждения количество','Availability Check':'проверка доступности','Standard Price':'стандартная цена','Moving Average Price':'среднескользящая цена','Split Valuation':'раздельная оценка','Invoice Verification':'контроль счетов','GR/IR':'ПМ/ПСч','Account Key':'ключ счета','Picking':'комплектование','Packing':'упаковка','Route':'маршрут','Delivery':'поставка','Billing':'фактурирование','Pricing':'расчет цены','Reservation':'резервирование','Supplier':'поставщик','Customer':'заказчик','G/L account':'основной счет','FI':'финансовый учет','SD':'сбыт','MM':'управление материальными потоками','S/4HANA':'SAP S/4HANA'}
# Expand abbreviations only where relevant: MM/SD/FI only when standalone in prose. Avoid translating technology name S/4HANA.
GLOSS.pop('MM');GLOSS.pop('SD');GLOSS.pop('FI');GLOSS.pop('S/4HANA')
GLOSS.update({'GR-based Invoice Verification':'контроль счетов на основе поступления материала','GR/IR Clearing Account':'счет ПМ/ПСч','Final Issue Indicator':'признак полной выдачи','Complete Delivery':'полная поставка','Partial Delivery':'частичная поставка','Cross-company-code Purchasing Organization':'централизованная закупочная организация','Invoice F2':'стандартная фактура','Pro Forma Invoice F8':'счет-проформа','Contract':'контракт','Scheduling Agreement':'соглашение о поставках','General Data':'общие данные','Company Code Data':'данные балансовой единицы','Purchasing Organization Data':'данные закупочной организации','Material Extension':'расширение материала','Time-dependent Conditions':'зависимые от времени условия','Time-dependent Conditions':'зависимые от времени условия','Time-independent Conditions':'независимые от времени условия','Account Category Reference':'ссылочный класс счетов','Valuation Type':'вид оценки','Valuation Area':'область оценки','Billing Relevance':'релевантность для фактурирования','Billing Cancellation':'аннулирование фактуры','Final Issue':'признак полной выдачи','Number Assignment':'вид нумерации','Supplier Master':'основная запись поставщика','Reconciliation Account':'контрольный счет','Payment Block':'блокировка для оплаты','Invoice Reversal':'сторно счета','Schedule Agreement':'соглашение о поставках','Pricing Type A':'тип расчета цены A','Pricing Type B':'тип расчета цены B','Pricing Type C':'тип расчета цены C','Pricing Type D':'тип расчета цены D','Pricing Type G':'тип расчета цены G','Pricing Type H':'тип расчета цены H'})
GLOSS_ITEMS=sorted(GLOSS.items(),key=lambda kv:-len(kv[0]))
TOKEN=re.compile(r'(?<![\w/])(?:'+ '|'.join(re.escape(x) for x,_ in GLOSS_ITEMS) +r')(?![\w/])')
def normalize_term(s):
    m=re.match(r'^(.*?)\s*\(([A-Za-z][A-Za-z0-9 /-]+)\)$',s)
    if m and m.group(2) in GLOSS and m.group(1).strip():
        return m.group(2)+' ('+m.group(1).strip().lower()+')'
    return s

def lang(s):
    # Single-pass replacement; prevents replacing a shorter term inside a longer translated name.
    return TOKEN.sub(lambda m: m.group(0) if s[m.end():].lstrip().startswith('(') else m.group(0)+' ('+GLOSS[m.group(0)]+')',s)

def stabletext(s):return lang(s.replace('ATP (Available-to-Promise)','ATP (доступное к подтверждению количество)')).replace('Конракт (','Контракт (')

def choose_distractors(facts,item,n=3):
    same=[x for x in facts if x['topic']==item['topic'] and x['term']!=item['term']]
    diff=[x for x in facts if x['term']!=item['term'] and x not in same]
    R.shuffle(same);R.shuffle(diff)
    return (same+diff)[:n]

def option(key,label,why,correct):return {'id':key,'label':stabletext(label),'correct':bool(correct),'feedback':stabletext(why)}

def facts_as_questions(facts,module):
    output=[]
    facts=[{**f,'term':normalize_term(f['term'])} for f in facts]
    for idx,f in enumerate(facts):
        others=choose_distractors(facts,f,3)
        entries=[f,*others];R.shuffle(entries)
        meaning=f['meaning'];case=f['case'];term=f['term']
        typ='single'
        opts=[option('ABCD'[i],e['term'],(f'Этот объект подходит: {meaning}.' if e is f else f'Этот объект служит другой цели: {e["meaning"]}.'),e is f) for i,e in enumerate(entries)]
        output.append({'module':module,'topic':f['topic'],'type':typ,'question':stabletext(f'В учебной системе SAP какой термин, объект или код точнее всего соответствует задаче: {meaning}?'),'options':opts,'explanation':stabletext(f'{term}: {meaning}. В диагностике сначала устанавливают тип объекта, затем выбирают соответствующую транзакцию или настройку.'),'source':'MM v2 + тесты' if module=='MM' else 'LO605/LO610/LO615/LO620/SCM620'})
        mode=idx%10
        if mode in (1,3,8):
            # situational multiselect; 2 valid descriptive statements, 2 deliberately mismatched
            a=f;b=others[0];c=others[1];d=others[2]
            pairs=[(a,a['meaning'],True),(b,b['meaning'],True),(c,d['meaning'],False),(d,c['meaning'],False)];R.shuffle(pairs)
            opts2=[option('ABCD'[i],f'{t["term"]} — {meaning}',('Связь верна: '+t['meaning'] if good else 'Это неверное соответствие; фактическое назначение: '+t['meaning'])+'.',good) for i,(t,meaning,good) in enumerate(pairs)]
            output.append({'module':module,'topic':f['topic'],'type':'multi','question':stabletext(f'В контексте задачи «{case}» консультант составляет памятку по связанным объектам SAP. Выберите ВСЕ верные соответствия.'),'options':opts2,'explanation':stabletext('Корректное соответствие означает, что описание действительно относится к указанному объекту, а не к другой транзакции или настройке.'),'source':'MM v2 + тесты' if module=='MM' else 'LO605/LO610/LO615/LO620/SCM620'})
        elif mode in (5,7,9):
            actual=(idx//10)%2==0;candidate=f if actual else others[0]
            claim=f'Для ситуации «{case}» наиболее подходящим объектом из перечисленных является {candidate["term"]}.'
            reason=(f'Для описанного действия подходит {term}: {meaning}.' if actual else f'В действительности требуется {term}: {meaning}. {candidate["term"]} используется для другой операции: {candidate["meaning"]}.')
            opts2=[option('true','Верно',('При выборе «Верно» следует признать утверждение точным. ' if actual else 'Выбор «Верно» неверен. ')+reason,actual),option('false','Неверно',('Выбор «Неверно» отклоняет верное утверждение. ' if actual else 'При выборе «Неверно» отмечается подмена объекта. ')+reason,not actual)]
            output.append({'module':module,'topic':f['topic'],'type':'tf','question':stabletext(claim),'options':opts2,'explanation':stabletext(reason),'source':'MM v2 + тесты' if module=='MM' else 'LO605/LO610/LO615/LO620/SCM620'})
        else:
            entries=[f,*others];R.shuffle(entries)
            opts2=[option('ABCD'[i],x['term'],(f'Выбор соответствует сценарию: {meaning}.' if x is f else f'Этот вариант предназначен для другой операции: {x["meaning"]}.'),x is f) for i,x in enumerate(entries)]
            output.append({'module':module,'topic':f['topic'],'type':'single','question':stabletext(f'Ситуационная задача. {case} Какой объект, параметр или транзакция решает поставленную задачу наиболее непосредственно?'),'options':opts2,'explanation':stabletext(f'Следует использовать {term}, потому что его назначение — {meaning}.'),'source':'MM v2 + тесты' if module=='MM' else 'LO605/LO610/LO615/LO620/SCM620'})
    return output

def calc_question(module,topic,stem,choices,key,explanation,source):
    correct=choices[key]
    opts=[option('ABCD'[i],ch,(explanation if i==key else f'Этот результат не соответствует условиям задачи. {explanation}'),i==key) for i,ch in enumerate(choices)]
    return {'module':module,'topic':topic,'type':'single','question':stabletext(stem),'options':opts,'explanation':stabletext(explanation),'source':source}

def numeric_cases_mm():
    out=[]
    # 12 distinct numerical/scenario templates, with rotating specific parameters
    for variant in range(3):
        rcv=[100,150,240][variant];invoice=[60,120,180][variant];left=rcv-invoice
        choices=[f'{left} шт. остаются несопоставленными',f'{rcv} шт. полностью закрыты',f'{invoice} шт. остаются несопоставленными','GR/IR всегда закрывается целиком'];R.shuffle(choices)
        out.append(calc_question('MM','GR/IR',f'В PO (заказе на поставку) заказано {rcv} шт., MIGO (движения материала) приняла {rcv} шт., MIRO (контроль счета) зарегистрировала только {invoice} шт. при контроле по поступлению. Какая часть количественного сопоставления GR/IR (ПМ/ПСч) остается открытой?',choices,choices.index(f'{left} шт. остаются несопоставленными'),f'По поступлению принято {rcv} шт., по счету сопоставлено {invoice} шт.; разница {rcv} − {invoice} = {left} шт.','MM v2: вопросы 11, 47, 50'))
        qty=[40,60,80][variant];standard=[100,125,140][variant];purchase=standard+[10,8,15][variant];diff=qty*(purchase-standard);value=qty*standard
        choices=[f'Запас {value} руб., ценовое отклонение {diff} руб.',f'Запас {qty*purchase} руб. без отклонения',f'Запас {diff} руб., отклонение {value} руб.','Списание всей суммы сразу в расходы'];R.shuffle(choices)
        out.append(calc_question('MM','Оценка',f'Материал имеет Standard Price (стандартную цену) S = {standard} руб./шт. Приход {qty} шт. по цене закупки {purchase} руб./шт. Налог и дополнительные расходы не рассматриваются. Каковы учетная стоимость прироста запаса и ценовое отклонение?',choices,choices.index(f'Запас {value} руб., ценовое отклонение {diff} руб.'),f'При S запас оценивается по стандартной цене: {qty} × {standard} = {value} руб. Разница = {qty} × ({purchase} − {standard}) = {diff} руб.','MM v2: вопросы 51–54'))
        old=[50,40,80][variant];new=[50,60,20][variant];pold=[100,80,150][variant];pnew=[120,100,100][variant];avg=(old*pold+new*pnew)/(old+new)
        choices=[f'{avg:g} руб./шт.',f'{pnew} руб./шт.',f'{pold} руб./шт.',f'{(pold+pnew)/2+5:g} руб./шт.'];R.shuffle(choices)
        out.append(calc_question('MM','Оценка',f'Материал управляется по Moving Average Price (среднескользящей цене) V. До поступления было {old} шт. по {pold} руб./шт.; поступило {new} шт. по {pnew} руб./шт. Без дополнительных расходов и округлений. Какова новая средняя цена?',choices,choices.index(f'{avg:g} руб./шт.'),f'Средневзвешенная цена = ({old} × {pold} + {new} × {pnew}) / ({old} + {new}) = {avg:g} руб./шт.','MM v2: вопросы 53–54'))
        reserv=[80,100,120][variant];issued=[55,70,90][variant];rem=reserv-issued
        choices=[f'{rem} шт. потребности можно закрыть Final Issue (признаком полной выдачи)',f'Нужно оформить фиктивный Goods Issue (отпуск материала) на {rem} шт.',f'Нужно создать PO (заказ на поставку) на {rem} шт.',f'Необходимо списать весь запас {reserv} шт. повторно'];R.shuffle(choices)
        out.append(calc_question('MM','Резервирования',f'Reservation (резервирование) создано на {reserv} шт. Реально выдано {issued} шт., остальные больше не нужны. Как закрыть резервирование без фиктивного материального движения?',choices,choices.index(f'{rem} шт. потребности можно закрыть Final Issue (признаком полной выдачи)'),f'Неиспользованная потребность {reserv} − {issued} = {rem} шт.; она закрывается признаком полной выдачи, а не искусственным расходом.','Материал: резервирования'))
        qty=[100,200,250][variant];po=[85,110,90][variant];inv=po+[5,8,4][variant];var=qty*(inv-po)
        choices=[f'Отклонение {var} руб.; проверить допуски и блокировку оплаты',f'Отклонение {qty*inv} руб.; немедленно сторнировать Goods Receipt (поступление материала)',f'Отклонение отсутствует, так как количество совпадает',f'Автоматически создать Credit Memo (кредитовое авизо) клиенту'];R.shuffle(choices)
        out.append(calc_question('MM','Счета',f'PO (заказ на поставку) содержит {qty} шт. по {po} руб., а входящий счет MIRO (контроль счетов) — {qty} шт. по {inv} руб. Что должен диагностировать бухгалтер?',choices,choices.index(f'Отклонение {var} руб.; проверить допуски и блокировку оплаты'),f'Разница за единицу {inv} − {po} = {inv-po} руб.; сумма отклонения {qty} × {inv-po} = {var} руб.','MM v2: контроль счетов'))
        q=[25,40,60][variant];p=[120,90,150][variant];total=q*p
        choices=[f'Дт запасы {total} / Кт GR/IR (ПМ/ПСч) {total}',f'Дт поставщик {total} / Кт выручка {total}',f'Дт GR/IR (ПМ/ПСч) {total} / Кт запасы {total}',f'Дт расходы {total} / Кт клиент {total}'];R.shuffle(choices)
        out.append(calc_question('MM','Автопроводки',f'Обычный оцененный Goods Receipt (поступление материала) по PO (заказу на поставку): {q} шт. × {p} руб. Какова типовая сторона проводки запасов и GR/IR (ПМ/ПСч), без налога и отклонений?',choices,choices.index(f'Дт запасы {total} / Кт GR/IR (ПМ/ПСч) {total}'),f'Поступление увеличивает активы на {total} руб., промежуточное обязательство по GR/IR (ПМ/ПСч) кредитуется на ту же сумму.','MM v2: вопросы 11, 47'))
        q=[20,35,50][variant];p=[300,200,160][variant];total=q*p
        choices=[f'Дт GR/IR (ПМ/ПСч) {total} / Кт поставщик {total}',f'Дт поставщик {total} / Кт GR/IR (ПМ/ПСч) {total}',f'Дт запасы {total} / Кт выручка {total}',f'Дт клиент {total} / Кт расходы {total}'];R.shuffle(choices)
        out.append(calc_question('MM','Счета',f'После оцененного поступления по PO (заказу на поставку) вводится MIRO (контроль счетов) на {q} шт. по {p} руб. (счет полностью совпадает с поступлением). Какая типовая проводка закрывает GR/IR (ПМ/ПСч)?',choices,choices.index(f'Дт GR/IR (ПМ/ПСч) {total} / Кт поставщик {total}'),f'Входящий счет дебетует счет GR/IR (ПМ/ПСч) и кредитует кредиторскую задолженность поставщика на {total} руб.','MM v2: вопросы 47, 50'))
        z=[10,20,30][variant];a=[50,80,100][variant];b=[60,90,110][variant];choices=[f'311: перенести {z} шт. между складами одного Plant (завода)',f'301: переместить {z} шт. между балансовыми единицами',f'101: принять {z} шт. от Supplier (поставщика)',f'261: списать {z} шт. на производственный заказ'];R.shuffle(choices)
        out.append(calc_question('MM','Движения',f'На одном Plant (заводе) требуется переместить {z} шт. со склада {a:04d} на склад {b:04d}, не меняя владельца и оценочную область. Какую операцию выбрать?',choices,choices.index(f'311: перенести {z} шт. между складами одного Plant (завода)'),f'Для одношагового движения между складами одного завода применяется вид движения 311.','Материал: перемещения запаса'))
        expected=[30,40,50][variant];actual=[20,25,30][variant];missing=expected-actual
        choices=[f'Сопоставить фактические {actual} шт. и ожидать последующую поставку {missing} шт.',f'Автоматически провести MIRO на полные {expected} шт.',f'Создать Credit Memo (кредитовое авизо) на {actual} шт. без проверки',f'Сторнировать все подтвержденные {actual} шт.'];R.shuffle(choices)
        out.append(calc_question('MM','Закупки',f'По PO (заказу на поставку) ожидается {expected} шт., но по MIGO (движению материала) фактически получено {actual} шт. Счет поставщика пока не поступил. Как трактовать ситуацию?',choices,choices.index(f'Сопоставить фактические {actual} шт. и ожидать последующую поставку {missing} шт.'),f'История PO (заказа на поставку) фиксирует частичный приход {actual} шт.; открытый остаток равен {missing} шт.','MM v2: вопросы 11, 35'))
        q=[10,20,30][variant];p=[50,70,90][variant];total=q*p
        choices=[f'Поставщик остается владельцем до потребления; при изъятии возникает обязательство на {total} руб.',f'Обязательство {total} руб. возникает автоматически при физическом приходе на консигнацию',f'Товар сразу становится собственностью компании при приеме',f'Необходимо применить движение 601 по исходящей поставке'];R.shuffle(choices)
        out.append(calc_question('MM','Запасы',f'На консигнационном складе поставщика находится {q} шт. по {p} руб. Компания изымает весь запас для собственного расхода. Каков основной принцип возникновения обязательства?',choices,choices.index(f'Поставщик остается владельцем до потребления; при изъятии возникает обязательство на {total} руб.'),f'Консигнационный запас остается собственностью поставщика до изъятия; задолженность образуется при потреблении на {total} руб.','MM: консигнация'))
        qty=[50,75,120][variant];oldprice=[110,80,95][variant];newprice=oldprice-[10,8,5][variant];amount=qty*(oldprice-newprice)
        choices=[f'Subsequent Credit (дополнительное кредитование) на {amount} руб.',f'Subsequent Debit (дополнительное дебетование) на {amount} руб.',f'Reversal (сторно) исходного счета на {qty*oldprice} руб.',f'Goods Receipt (поступление материала) на {qty} шт.'];R.shuffle(choices)
        out.append(calc_question('MM','Счета',f'MIRO (контроль счетов): ранее проведен корректный входящий счет на {qty} шт. по {oldprice} руб./шт. После согласования поставщик снижает цену до {newprice} руб./шт. без возврата товара и без отмены исходного счета. Что провести?',choices,choices.index(f'Subsequent Credit (дополнительное кредитование) на {amount} руб.'),f'Последующее кредитование снижает стоимость того же количества на {qty} × ({oldprice} − {newprice}) = {amount} руб.','MM v2: контроль счетов'))
        qty=[60,90,120][variant];two=[15,30,40][variant];rem=qty-two
        choices=[f'После первого отпуска резервирование сохраняет {rem} шт. открытой потребности',f'Резервирование уничтожается после любого частичного отпуска',f'Вся потребность в {qty} шт. считается физически выданной',f'Оставшиеся {rem} шт. автоматически приходят на склад'];R.shuffle(choices)
        out.append(calc_question('MM','Резервирования',f'Reservation (резервирование) на {qty} шт., разрешающее частичную выдачу. Со склада оформлен Goods Issue (отпуск материала) на {two} шт., Final Issue (признак полной выдачи) не установлен. Какой остаток потребности?',choices,choices.index(f'После первого отпуска резервирование сохраняет {rem} шт. открытой потребности'),f'Остаток потребности составляет {qty} − {two} = {rem} шт.; физический расход и плановая потребность обновляются раздельно.','Материал: резервирования'))
    return out

def numeric_cases_sd():
    out=[]
    for variant in range(2):
        ordqty=[100,150][variant];stock=[60,90][variant];rest=ordqty-stock
        opts=[f'Подтвердить {stock} шт. на эту дату, оставшиеся {rest} шт. — по доступности позднее',f'Подтвердить все {ordqty} шт. только на основании общего заказа',f'Создать Invoice F2 (стандартную фактуру) на {ordqty} шт.',f'Обнулить все Schedule Lines (строки графика)'];R.shuffle(opts)
        out.append(calc_question('SD','ATP',f'По Sales Order (заказу клиента) запрошено {ordqty} шт. на одну дату, подтвержденная ATP (доступность для подтверждения) на эту дату — {stock} шт., позже ожидается поступление. Какое решение соответствует проверке доступности?',opts,opts.index(f'Подтвердить {stock} шт. на эту дату, оставшиеся {rest} шт. — по доступности позднее'),f'На требуемую дату доступно {stock} шт., неудовлетворенная часть {ordqty} − {stock} = {rest} шт. требует проверки будущих дат.','LO605'))
        qty=[40,60][variant];billed=[130,125][variant];agreed=[120,110][variant];credit=qty*(billed-agreed)
        opts=[f'Credit Memo (кредитовое авизо) на {credit} руб.',f'Debit Memo (дебетовое авизо) на {credit} руб.',f'Invoice F2 (фактура) на {qty*billed} руб.',f'Goods Receipt (поступление материала) на {qty} шт.'];R.shuffle(opts)
        out.append(calc_question('SD','Рекламации',f'Клиенту продали {qty} шт. по ошибочной цене {billed} руб./шт., согласованная цена {agreed} руб./шт. Товар не возвращается. Как корректировать задолженность?',opts,opts.index(f'Credit Memo (кредитовое авизо) на {credit} руб.'),f'Излишне начислено {qty} × ({billed} − {agreed}) = {credit} руб.; кредитовое авизо уменьшает долг клиента.','LO615'))
        qty=[20,30][variant];billed=[90,80][variant];correct=[100,95][variant];debit=qty*(correct-billed)
        opts=[f'Debit Memo (дебетовое авизо) на {debit} руб.',f'Credit Memo (кредитовое авизо) на {debit} руб.',f'Сторно Goods Issue (отпуска материала) на {qty} шт.',f'Invoice F2 (фактура) на {qty*billed} руб. без корректировки'];R.shuffle(opts)
        out.append(calc_question('SD','Рекламации',f'Выписана фактура на {qty} шт. по {billed} руб., но договорная цена {correct} руб./шт. Клиент согласен доплатить. Какой документ подходит?',opts,opts.index(f'Debit Memo (дебетовое авизо) на {debit} руб.'),f'Недоначисление составляет {qty} × ({correct} − {billed}) = {debit} руб.; дебетовое авизо увеличивает дебиторскую задолженность.','LO615'))
        qty=[70,110][variant];step=[20,25][variant];free=[2,3][variant];bonus=(qty//step)*free
        opts=[f'{bonus} бесплатных шт.',f'{free} бесплатных шт.',f'{qty//step+free} бесплатных шт.',f'{(qty+step-1)//step*free} бесплатных шт.'];R.shuffle(opts)
        out.append(calc_question('SD','Натуральный рабат',f'Exclusive Free Goods (исключенный натуральный рабат): за каждые полные {step} шт. заказанного товара предоставляется {free} бесплатных шт. Клиент заказывает {qty} шт. Сколько бесплатных единиц?',opts,opts.index(f'{bonus} бесплатных шт.'),f'Число полных групп: {qty} // {step} = {qty//step}; бонус: {qty//step} × {free} = {bonus} шт.','LO620/SCM620'))
        base=[10000,18000][variant];disc=[10,15][variant];tax=20;net=base*(100-disc)/100;gross=net*1.2
        opts=[f'{gross:g} руб.',f'{net:g} руб.',f'{base*1.2:g} руб.',f'{base*(1-disc/200):g} руб.'];R.shuffle(opts)
        out.append(calc_question('SD','Pricing',f'База PR00 = {base} руб., скидка {disc}% применяется до налога, налог MWST = {tax}% от стоимости после скидки. Чему равна итоговая сумма к оплате?',opts,opts.index(f'{gross:g} руб.'),f'После скидки {base} × (1 − {disc}/100) = {net:g}; с налогом × 1,20 = {gross:g} руб.','LO620/SCM620'))
        turnover=[200000,350000][variant];pct=[3,4][variant];reb=turnover*pct//100
        opts=[f'{reb} руб.',f'{turnover} руб.',f'{pct*100} руб.',f'{turnover+reb} руб.'];R.shuffle(opts)
        out.append(calc_question('SD','Бонусы',f'Rebate Agreement (соглашение о бонусе) предусматривает {pct}% от релевантного оборота. Billing Documents (документы фактуры) сформировали базу {turnover} руб. Каков бонус без иных ограничений?',opts,opts.index(f'{reb} руб.'),f'Бонус составляет {turnover} × {pct}% = {reb} руб. В процессе расчета учитываются начисления и кредитование клиента.','SCM620'))
        qty1=[40,60][variant];qty2=[30,50][variant];total=qty1+qty2;minq=[65,100][variant];eligible=total>=minq
        opts=[('Шкала скидки по сумме количеств обеих позиций срабатывает' if eligible else 'Шкала по объединенному количеству еще не достигает порога'),('Скидка считается только по первой позиции и всегда достигает порога'),('Две позиции нельзя объединить даже при одинаковой KONDM (группе расчета цены материала)'),('Должен быть создан отдельный Credit Memo (кредитовое авизо)')];R.shuffle(opts)
        key=opts.index('Шкала скидки по сумме количеств обеих позиций срабатывает' if eligible else 'Шкала по объединенному количеству еще не достигает порога')
        out.append(calc_question('SD','Group Condition',f'Две позиции имеют одну KONDM (группу расчета цены материала): {qty1} и {qty2} шт. Group Condition (групповое условие) со шкалой от {minq} шт. агрегирует обе позиции. Что произойдет?',opts,key,f'Общее количество {qty1} + {qty2} = {total} шт.; порог {minq} шт. '+('достигнут.' if eligible else 'не достигнут.'),'SCM620'))
        alloc=[(70,30,2000),(60,40,3000)][variant];a,b,tot=alloc;part=tot*a//100
        opts=[f'{part} руб. на первую позицию',f'{tot} руб. на каждую позицию',f'{tot-part} руб. на первую позицию',f'{tot*a} руб. на первую позицию'];R.shuffle(opts)
        out.append(calc_question('SD','Pricing',f'HM00 (ручная общая стоимость заказа) установлено на {tot} руб. База распределения по позициям: первая {a}%, вторая {b}%. Сколько отнести на первую позицию при пропорциональном распределении?',opts,opts.index(f'{part} руб. на первую позицию'),f'Пропорциональная доля: {tot} × {a}% = {part} руб.','SCM620'))
    return out

def build():
    mm=facts_as_questions(parse(MM),'MM')+numeric_cases_mm()
    sd=facts_as_questions(parse(SD),'SD')+numeric_cases_sd()
    # 214+36=250; 234+16=250
    assert len(mm)==250,(len(mm),len(sd));assert len(sd)==250
    R.shuffle(mm);R.shuffle(sd)
    for i,q in enumerate(mm+sd,1):q['id']=i
    bank=mm+sd
    assert all(len(q['options']) in [2,4] for q in bank)
    assert all(sum(bool(o['correct']) for o in q['options'])==1 if q['type']!='multi' else sum(bool(o['correct']) for o in q['options'])>=2 for q in bank)
    assert len({q['question'] for q in bank})==500
    output=ROOT/'data/questions.json';output.write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Generated',len(bank),Counter(q['module'] for q in bank),Counter(q['type'] for q in bank),'situational',sum('Ситуаци' in q['question'] or 'Ситуационная' in q['question'] for q in bank), 'size',output.stat().st_size)
if __name__=='__main__':build()
