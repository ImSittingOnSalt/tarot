import telebot
import sqlite3
import random
from datetime import datetime, timedelta
from telebot import types

bot = telebot.TeleBot('-')
ADMIN_CHAT_ID = -
FEEDBACK_DB = 'feedback.sqlite3'

def init_feedback_db(): # Инициализация БД для фидбэка
  conn = sqlite3.connect(FEEDBACK_DB)
  cursor = conn.cursor()
  cursor.execute('''CREATE TABLE IF NOT EXISTS feedback
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  username TEXT,
                  text TEXT,
                  created_at TIMESTAMP,
                  admin_reply TEXT DEFAULT NULL)''')
  conn.commit()
  conn.close()
init_feedback_db()

@bot.message_handler(commands=['start'])
def start(message):
  conn = sqlite3.connect('tarot.sqlite3')
  cur = conn.cursor()
  markup = types.ReplyKeyboardMarkup()
  btn1 = types.KeyboardButton('Значения карт')
  btn2 = types.KeyboardButton('Карта дня')
  btn3 = types.KeyboardButton('Виды раскладов')
  btn4 = types.KeyboardButton('Связи между картами')
  btn5 = types.KeyboardButton('Расширить возможности')
  btn6 = types.KeyboardButton('Помощь')
  btn7 = types.KeyboardButton('Обратная связь')
  markup.row(btn1, btn2)
  markup.row(btn3, btn4)
  markup.row(btn5, btn6)
  markup.row(btn7)

  welcome_text = (
    f"✨ <b>Добро пожаловать, {message.from_user.first_name}!</b> ✨\n\n"
    f"Я - ваш цифровой помощник в мире Таро. 🔮\n\n"
    f"Мои возможности:\n"
    f"• Гадания на картах Таро\n"
    f"• Толкования значений карт\n"
    f"• Уникальные расклады\n\n"
    f"Выберите действие в <b>меню</b> или нажмите /help, чтобы увидеть все команды.\n\n"
    f"Давайте начнём наше магическое путешествие! 🌙"
  )

  bot.send_message(message.chat.id, welcome_text, parse_mode="html", reply_markup=markup)
  #bot.reply_to(message, f"Ваш ID: `{message.chat.id}`", parse_mode='Markdown')
  bot.register_next_step_handler(message, on_click)

def on_click(message):
  if message.text.lower() == 'значения карт':
    decks(message)
    bot.register_next_step_handler(message, on_click)
  elif message.text.lower() == 'карта дня':
    card = get_daily_card()
    if card:
        send_card_info(message.chat.id, card)
    else:
        bot.reply_to(message, "❌ Не удалось получить карту дня. Попробуйте позже.")
    bot.register_next_step_handler(message, on_click)
  elif message.text.lower() == 'виды раскладов':
    spreads(message)
    bot.register_next_step_handler(message, on_click)
  elif message.text.lower() == 'связи между картами':
    custom_spread(message)
    bot.register_next_step_handler(message, on_click)
  elif message.text.lower() == 'расширить возможности':
    buy_deck(message)
    bot.register_next_step_handler(message, on_click)
  elif message.text.lower() == 'помощь':
    help(message)
    bot.register_next_step_handler(message, on_click)
  elif message.text.lower() == 'обратная связь':
    feedback(message)
  else:
    bot.reply_to(message, '<em>Пожалуйста, воспользуйтесь меню для выбора команды</em>', parse_mode='html')
    bot.register_next_step_handler(message, on_click)
  
@bot.message_handler(commands=['decks'])#
def decks(message):
  markup = types.InlineKeyboardMarkup()
  btn1 = types.InlineKeyboardButton('Уэйта', callback_data = 'wate')
  btn2 = types.InlineKeyboardButton('Тёмная', callback_data = 'dark')
  btn3 = types.InlineKeyboardButton('Тота', callback_data = 'dark')
  btn4 = types.InlineKeyboardButton('Марсельская', callback_data = 'dark')
  markup.row(btn1, btn2)
  markup.row(btn3, btn4)
  bot.send_message(message.chat.id, 'Выбери интересующую тебя колоду таро', reply_markup=markup)

@bot.callback_query_handler(func=lambda callback: True) # добавить картинки раскладам, добавить в тексты про энергообмен
def callback_message(callback):
  markup = types.InlineKeyboardMarkup()
  
  ####################### коллбэк для decks ################################
  if callback.data in ['wate', 'dark', 'toth', 'mars']:
    if callback.data == 'wate':
      deck_name = 'Уэйт'
      prefix = 'w'
    elif callback.data == 'dark':
      deck_name = 'Тёмная'
      prefix = 'd'
    elif callback.data == 'toth':
      deck_name = 'Тота'
      prefix = 't'
    elif callback.data == 'mars':
      deck_name = 'Марсельская'
      prefix = 'm'
    
    bot.delete_message(callback.message.chat.id, callback.message.message_id)
    
    btn1 = types.InlineKeyboardButton('Старшие Арканы', callback_data=f'{prefix}_arc')
    btn2 = types.InlineKeyboardButton('Мечи', callback_data=f'{prefix}_sword')
    btn3 = types.InlineKeyboardButton('Жезлы', callback_data=f'{prefix}_wand')
    btn4 = types.InlineKeyboardButton('Пентакли', callback_data=f'{prefix}_pentacle')
    btn5 = types.InlineKeyboardButton('Кубки', callback_data=f'{prefix}_cup')
    
    markup.row(btn1)
    markup.row(btn2, btn3)
    markup.row(btn4, btn5)
    
    bot.send_message( callback.message.chat.id,
                    f'Колода: {deck_name}\nВыбери масть карты:', 
                    reply_markup=markup
    )
    return
  
  parts = callback.data.split('_') # Разбираем префикс из callback_data
  if len(parts) != 2:
    return
  prefix, card_type = parts
  
  # Обработка выбора типа карт
  if card_type == 'arc': # Старшие арканы
    markup = types.InlineKeyboardMarkup(row_width=4) 
    
    cards = [
      ('0. Дурак', f'{prefix}_fool'),
      ('I. Маг', f'{prefix}_magician'),
      ('II. Верховная Жрица', f'{prefix}_high_priestess'),
      ('III. Императрица', f'{prefix}_empress'),
      ('IV. Император', f'{prefix}_emperor'),
      ('V. Иерофант', f'{prefix}_hierophant'),
      ('VI. Влюблённые', f'{prefix}_lovers'),
      ('VII. Колесница', f'{prefix}_chariot'),
      ('VIII. Сила', f'{prefix}_strength'),
      ('IX. Отшельник', f'{prefix}_hermit'),
      ('X. Колесо Фортуны', f'{prefix}_wheel_of_fortune'),
      ('XI. Справедливость', f'{prefix}_justice'),
      ('XII. Повешенный', f'{prefix}_hanged_man'),
      ('XIII. Смерть', f'{prefix}_death'),
      ('XIV. Умеренность', f'{prefix}_temperance'),
      ('XV. Дьявол', f'{prefix}_devil'),
      ('XVI. Башня', f'{prefix}_tower'),
      ('XVII. Звезда', f'{prefix}_star'),
      ('XVIII. Луна', f'{prefix}_moon'),
      ('XIX. Солнце', f'{prefix}_sun'),
      ('XX. Суд', f'{prefix}_judgement'),
      ('XXI. Мир', f'{prefix}_world')
    ]
    
    buttons = [types.InlineKeyboardButton(text, callback_data=cb) for text, cb in cards]
    markup.add(*buttons)
    
    bot.edit_message_text( "Выберите старший аркан:", callback.message.chat.id, callback.message.message_id, reply_markup=markup)
  
  elif card_type in ['sword', 'wand', 'cup', 'pentacle']: # Младшие арканы
    markup = types.InlineKeyboardMarkup(row_width=4) 
    
    cards = [
      ('Туз', f'{prefix}_ace_{card_type}'),
      ('2', f'{prefix}_2_{card_type}'),
      ('3', f'{prefix}_3_{card_type}'),
      ('4', f'{prefix}_4_{card_type}'),
      ('5', f'{prefix}_5_{card_type}'),
      ('6', f'{prefix}_6_{card_type}'),
      ('7', f'{prefix}_7_{card_type}'),
      ('8', f'{prefix}_8_{card_type}'),
      ('9', f'{prefix}_9_{card_type}'),
      ('10', f'{prefix}_10_{card_type}'),
      ('Паж', f'{prefix}_page_{card_type}'),
      ('Рыцарь', f'{prefix}_knight_{card_type}'),
      ('Королева', f'{prefix}_queen_{card_type}'),
      ('Король', f'{prefix}_king_{card_type}')
    ]
    
    # Разбиваем на строки по 4 кнопки
    for i in range(0, len(cards), 4):
      row = cards[i:i+4]
      markup.row(*[types.InlineKeyboardButton(text, callback_data=cb) for text, cb in row])
    
    # Получаем русское название масти
    suit_name = {
      'sword': 'Мечи',
      'wand': 'Жезлы',
      'cup': 'Кубки',
      'pentacle': 'Пентакли'
    }.get(card_type, '')
    
    bot.edit_message_text(f"Выберите карту масти {suit_name}:", callback.message.chat.id, callback.message.message_id, reply_markup=markup
    )
  
  # Обработка выбора конкретной карты
  elif any(x in callback.data for x in ['fool', 'magician', 'ace_', 'page_', '2_', '3_']):
    # Здесь будет обработка выбора конкретной карты
    card_name = callback.data.replace(f'{prefix}_', '')
    bot.answer_callback_query(callback.id, f"Выбрана карта: {card_name}")

  ####################### коллбэк для spreads ################################
  parts = callback.data.split('_')
  if len(parts) != 2:
    return
  prefix, spread_type = parts
  
  if prefix == 'sp':
    spreads_text = {
      'sp_day': {
        'text': (
          "🔮 <b>Карта Дня</b>\n\n"
          "<b>Задача:</b> Получить совет или предупреждение на текущие сутки.\n\n"
          "<b>Как трактовать:</b>\n"
          "• Прямое положение — ключевая энергия дня\n"
          "• Перевёрнутое — на что обратить особое внимание"
        )
      },
      'sp_three': {
        'text': (
          "🌱 <b>Расклад Три карты</b> (Прошлое-Настоящее-Будущее)\n\n"
          "<b>Задача:</b> Понять развитие ситуации.\n\n"
          "<b>Значение позиций:</b>\n"
          "• <em>Прошлое</em> — корень текущей ситуации\n"
          "• <em>Настоящее</em> — актуальные обстоятельства\n"
          "• <em>Будущее</em> — вероятный исход (при сохранении текущего курса)\n\n"
          "<b>Пример:</b> Если в будущем выпал Суд — ждите важных решений. Башня — резкие изменения."
        )
      },
      'sp_rel': {
        'text': (
          "❤️ <b>Расклад на отношения \"Двое\"</b>\n\n"
          "<b>Задача:</b> Проанализировать связь между партнёрами.\n\n"
          "<b>Структура расклада:</b>\n"
          "1. Карта 1 (Вы)\n"
          "2. Карта 2 (Партнёр)\n"
          "3. Карта 3 (Что вас объединяет)\n"
          "4. Карта 4 (Препятствия)\n"
          "5. Карта 5 (Перспективы)\n\n"
          "<b>Особые карты:</b>\n"
          "• Влюблённые — глубокая связь\n"
          "• 4 Кубков — неудовлетворённость\n"
          "• Рыцарь Мечей — конфликты"
        )
      },
      'sp_kel': {
        'text': (
          "🏰 <b>Кельтский Крест (10 карт)</b>\n\n"
          "<b>Задача:</b> Всесторонний анализ проблемы.\n\n"
          "<b>Ключевые позиции:</b>\n"
          "1. Суть вопроса (центральная карта)\n"
          "2. Препятствие (пересекает первую)\n"
          "3. Сознательные мысли\n"
          "4. Подсознательные мотивы\n"
          "5. Ближайшее будущее\n\n"
          "<i>История:</i> Один из старейших раскладов, использовался кельтскими жрецами."
        )
      },
      'sp_choice': {
        'text': (
          "💼 <b>Расклад \"Выбор\" (7 карт)</b>\n\n"
          "<b>Задача:</b> Сравнить 2 варианта решений.\n\n"
          "<b>Структура:</b>\n"
          "Вариант А → 1│2│3\n"
          "Вариант Б → 4│5│6\n"
          "7 → Что объединяет оба пути\n\n"
          "<b>Как читать:</b>\n"
          "• Император в столбце А — стабильность\n"
          "• Шут в столбце Б — неожиданные повороты"
        )
      },
      'sp_moon': {
        'text': (
          "🌙 <b>Расклад \"Полнолуние\" (12 карт по кругу)</b>\n\n"
          "<b>Задача:</b> Прогноз на месяц.\n\n"
          "<b>Особенности:</b>\n"
          "• Каждая карта — аспект жизни (работа, здоровье, отношения)\n"
          "• Луна в центре — общая энергия периода"
        )
      },
      'sp_advice': {
        'text': (
          "🎯 <b>Совет от Таро (1-3 карты)</b>\n\n"
          "<b>Задача:</b> Получить рекомендацию.\n\n"
          "<b>Варианты:</b>\n"
          "• Сила — проявите терпение\n"
          "• Колесо Фортуны — доверьтесь течению событий"
        )
      },
      'sp_dir1': {
        'text': (
          "📚 <b>Справочник таролога</b>\n\n"
          "<b>🔍 Как работает Таро?</b>\n"
          "Таро — это система символов, работающая через:\n"
          "• Подсознание — карты отражают скрытые мысли\n"
          "• Синхроничность — принцип \"значимых совпадений\"\n"
          "• Архетипы — универсальные образы\n\n"
          "<em>Например:</em> Карта Звезда говорит о надежде, в любви — духовная связь, в работе — творческий подъем.\n\n"
          "<b>⚠️ Что нельзя делать с Таро?</b>\n"
          "<b>1. Вопросы \"Да-Нет\"</b>\n — <em>Почему:</em> Таро показывает тенденции, а не бинарные ответы. Вместо <em>\"Получу ли я работу?\"</em> лучше спросить: <em>\"Что поможет успешно пройти собеседование?\"</em>\n"
          "<b>2. Гадать на срок >1 года</b>\n — <em>Причина:</em> Энергии слишком изменчивы. Точность прогноза резко падает.\n"
          "<b>3. Задавать один вопрос многократно</b>\n — <em>Эффект:</em> Карты начинают показывать хаос из-за \"энергетического шума\".\n"
          "<b>4. Гадать без согласия человека</b> (кроме случаев, когда он физически недоступен).\n\n"
          "<b>🌟 Как повысить точность раскладов?</b>\n"
          "<b>1. Четкий запрос</b>\n Не <em>\"Что меня ждёт?\"</em>, а <em>\"Какие перспективы у моего проекта до конца квартала?\"</em>\n"
          "<b>2. Правильное состояние</b>\n"
          "— Не гадать в стрессе/болезни/состоянии алкогольного опьянения\n"
          "— Перед раскладом для правильного настроя можно зажечь свечу или сделать 3 глубоких вдоха\n"
          "<b>3. Учитывать перевёрнутые карты</b>\n"
          "<em>Нюанс:</em> Не все колоды используют инверсии. Например, в <em>Таро Тота Кроули</em> их нет."
          "\n\n📖 <b>Особые случаи</b>\n\n"
          "<b>1. Карта Смерть</b>\n"
          "<em>Не буквально:</em> Почти всегда означает трансформацию, а не физическую смерть.\n\n"
          "<b>2. Карта Дьявол</b> в любви\n"
          "<em>Трактовка:</em> Не \"зло\", а зависимость или страсть без духовной связи.\n\n"
          "<b>Пустая колода</b> (если карты выпадают рубашкой вверх)\n"
          "<em>Что делать:</em> Прервать сеанс — это знак энергетического блокирования.\n\n"
        )
      },
      'sp_dir2': {
        'text': (
          "💡 <b>Полезные практики</b>\n"
          "• Ведение дневника — записывайте расклады и их реальные воплощения.\n"
          "• Очистка колоды — раз в месяц кладите карты под лунный свет.\n"
          "• Работа с позициями — в сложных раскладах сначала интерпретируйте каждую карту отдельно, затем их сочетания.\n\n"
          "📜 <b>Мантический этикет и психология работы с клиентами</b>\n"
          "<b>🔮 1. Этические правила таролога</b>\n"
          "✅ Можно:\n"
          "• Давать <b>советы</b>, но оставлять право выбора за клиентом.\n"
          "• Говорить о <b>тенденциях</b>, а не о фатальной предопределённости.\n"
          "• Гадать на себя в любое время (но без фанатизма).\n\n"
          "❌ Нельзя:\n"
          "• Пугать клиента («Тебя ждёт страшная болезнь!»).\n"
          "• Гадать за других без их согласия (например, на партнёра, который не знает об этом).\n"
          "• Давать <b>медицинские/юридические</b> прогнозы (это не компетенция Таро).\n"
          "• Навязывать повторные платные сеансы («Ты в опасности, купи ещё расклад!»).\n\n"
          "<b>💬 2. Психологические аспекты работы с клиентом</b>\n"
          "<b>🔹 Как задавать вопросы?</b>\n"
          "<em>❌ «Ты скоро разведешься?»</em> → Давление, может спровоцировать тревогу.\n"
          "<em>✅ «Что поможет укрепить ваши отношения?»</em> → Конструктивно, без запугивания.\n"
          "<b>🔹 Если выпали «тяжёлые» карты (Башня, 3 Мечей, Дьявол):</b>\n"
          "• Не говорите: <em>«Всё плохо, ты обречён».</em>\n"
          "• Лучше: <em>«Эта карта говорит о сложном периоде, но даёт шанс переосмыслить ситуацию».</em>\n"
          "<b>🔹 Если клиент в стрессе:</b>\n"
          "• Сначала успокойте: <em>«Давайте разберёмся, это не приговор».</em>\n"
          "• Избегайте категоричных формулировок.\n"
          "<b>🔹 Если клиент требует «гарантий»:</b>\n"
          "• Объясните: <em>«Таро показывает тенденции, но итог зависит от ваших действий».</em>\n\n"
          "<b>🌿 3. Личные границы таролога</b>\n"
          "• Не гадать, если чувствуете усталость или раздражение.\n"
          "• Прервать сеанс, если клиент агрессивен или требует невозможного.\n"
          "• Не брать на себя ответственность за чужую жизнь («Ты должен поступить именно так!»)."
        )
      }
    }

  if callback.data in spreads_text:
    spread_data = spreads_text[callback.data]
    bot.send_message( callback.message.chat.id, spread_data['text'], parse_mode='html', reply_markup=markup)

@bot.message_handler(commands=['daily']) #добавить фото, таймер, вид колоды
def daily_command(message):
    card = get_daily_card()  # Используем отдельную функцию для получения карты
    if not card:
        bot.reply_to(message, "❌ Не удалось получить карту дня. Попробуйте позже.")
        return
    
    send_card_info(message.chat.id, card)

def get_daily_card():
    conn = sqlite3.connect('tarot.sqlite3')
    cursor = conn.cursor()
    
    random_card_id = random.randint(1, 312)
    
    cursor.execute("""
        SELECT 
            c.card_name,
            c.card_number,
            c.arcana_type,
            c.suit,
            dc.image_url,
            m.daily_meaning,
            m.keywords,
            m.general_upright,
            m.general_reversed
        FROM 
            meanings m
        JOIN 
            deck_cards dc ON m.deck_card_id = dc.id
        JOIN 
            cards c ON dc.card_id = c.id
        WHERE 
            m.deck_card_id = ?
    """, (random_card_id,))
    
    card_data = cursor.fetchone()
    conn.close()
    
    if card_data:
        return {
            'name': card_data[0],
            'number': card_data[1],
            'arcana': card_data[2],
            'suit': card_data[3],
            'image_url': card_data[4],
            'daily_meaning': card_data[5],
            'keywords': card_data[6],
            'general_upright': card_data[7],
            'general_reversed': card_data[8]
        }
    return None

def send_card_info(chat_id, card):
  card_text = (
    f"✨ <b>Карта дня:</b> {card['name']}\n"
    f"🔢 <b>Номер:</b> {card['number']}\n"
    f"🎴 <b>Масть:</b> {card['suit'] if card['suit'] else 'Старший аркан'}\n\n"
    f"📜 <b>Значение карты дня:</b>\n{card['daily_meaning']}\n\n"
    f"🔑 <b>Ключевые слова:</b> {card['keywords']}"
  )
  
  #if card['image_url']:
  #  bot.send_photo(chat_id, card['image_url'], caption=card_text, parse_mode="HTML")
  #else:
  #  bot.send_message(chat_id, card_text, parse_mode="HTML")
  bot.send_message(chat_id, card_text, parse_mode="HTML")

@bot.message_handler(commands=['spreads'])#изменить текст сообщения
def spreads(message):
  markup = types.InlineKeyboardMarkup(row_width=2)
  
  buttons = [
      ('Расклад Карта Дня', 'sp_day'),
      ('Расклад Три карты', 'sp_three'),
      ('Расклад на отношения', 'sp_rel'),
      ('Расклад Кельтский Крест', 'sp_kel'),
      ('Расклад Выбор', 'sp_choice'),
      ('Расклад Полнолуние', 'sp_moon'),
      ('Расклад Совет от Таро', 'sp_advice'),
      ('Справочник таролога 1', 'sp_dir1'),
      ('Справочник таролога 2', 'sp_dir2')
  ]
  
  # Разбиваем на строки по 2 кнопки
  for i in range(0, len(buttons), 2):
      row = buttons[i:i+2]
      markup.row(*[types.InlineKeyboardButton(text, callback_data=cb) for text, cb in row])

  bot.send_message(message.chat.id, 'spreads', reply_markup=markup)

@bot.message_handler(commands=['custom_spread'])#
def custom_spread(message):
  bot.send_message(message.chat.id, 'custom_spread')

@bot.message_handler(commands=['buy_deck'])#
def buy_deck(message):
  bot.send_message(message.chat.id, 'buy_deck')

@bot.message_handler(commands=['help'])#отредачить текст
def help(message):
  help_text = (
    f"📜 <b>Список команд помощника таролога</b>\n\n"
  
    f"🔹 <b>Основные команды</b>\n"
    f"/start – запуск бота, краткое описание\n"
    f"/help – список всех команд\n"
    f"/decks – доступные колоды для работы\n\n"
    
    f"🔮 <b>Работа с картами</b>\n"
    f"/card – случайная карта (бесплатно – Уэйт)\n"
    f"/meaning – узнать значение карты (прямое/перевёрнутое):\n"
    f"  • Общее толкование\n"
    f"  • Толкование в любви\n"
    f"  • Значение как карты дня\n"
    f"(выбор колоды после команды)\n"
    f"/daily – карта дня (бесплатно – Уэйт)\n\n"
    
    f"🃏 <b>Расклады</b>\n"
    f"/spreads – список видов раскладов (описание, советы, фото)\n"
    f"/custom_spread – вручную выбрать карты и получить трактовку их сочетаний\n"
    f"/buy_deck – купить доступ к новым колодам и справочным материалам\n\n"
    
    f"⚙️ <b>Дополнительно</b>\n"
    f"/feedback – отзыв или предложение\n\n"
    
    f"(Бот учитывает различия колод и даёт детальные трактовки!)\n\n"
    
    f"💎 <b>Премиум:</b> Доступ ко всем справочным материалам и колодам Тота, Марсельской, Теней и др. через /buy_deck.\n\n"
    f"Готов к работе? Нажми /start! 🔍✨"
  ) 
  bot.send_message(message.chat.id, help_text, parse_mode='html')

@bot.message_handler(commands=['feedback']) # подробнее потестить ответы(от других людей? мб дело в том, что я сама пишу отзывы и они мне же приходят), добавить отмену написания отзыва
def feedback(message):
  conn = sqlite3.connect('feedback.sqlite3')
  cursor = conn.cursor()
  
  # Проверка ограничения (1 отзыв в час)
  #cursor.execute("SELECT created_at FROM feedback WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (message.from_user.id,))
  #last_feedback = cursor.fetchone()
  #if last_feedback and (datetime.now() - datetime.strptime(last_feedback[0], '%Y-%m-%d %H:%M:%S')) < timedelta(hours=1):
  #  bot.send_message(message.chat.id, "⏳ Вы уже отправляли отзыв недавно. Пожалуйста, попробуйте позже.")
  #  conn.close()
  #  bot.register_next_step_handler(message, on_click) # После отправки сообщения о лимите, регистрируем обработчик для продолжения работы
  #  return
  
  msg = bot.send_message(message.chat.id, "💬 Пожалуйста, напишите ваш отзыв или предложение:")
  msg.is_feedback = True # Помечаем сообщение как часть процесса фидбэка
  bot.register_next_step_handler(msg, process_feedback)

def process_feedback(message):
  conn = sqlite3.connect('feedback.sqlite3')
  cursor = conn.cursor()
  message.is_feedback = True # Помечаем сообщение как часть процесса фидбэка
  
  cursor.execute("INSERT INTO feedback (user_id, username, text, created_at) VALUES (?, ?, ?, ?)",
                (message.from_user.id, message.from_user.username, message.text, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
  conn.commit() # Сохраняем в БД
  feedback_id = cursor.lastrowid
  
  markup = types.InlineKeyboardMarkup()
  markup.add(types.InlineKeyboardButton("✍️ Ответить", callback_data=f"reply_{feedback_id}"))
  
  feedback_text = (
    f"📩 <b>Новый отзыв</b> (#{feedback_id})\n\n"
    f"👤 <b>Пользователь:</b> @{message.from_user.username} (<code>{message.from_user.id}</code>)\n"
    f"🕒 <b>Дата:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
    f"📝 <b>Сообщение:</b>\n<code>{message.text}</code>"
  )
  bot.send_message(ADMIN_CHAT_ID, feedback_text, parse_mode="HTML", reply_markup=markup)
  
  bot.send_message(message.chat.id, "✅ Спасибо! Ваш отзыв отправлен администратору.")
  conn.close()
  bot.register_next_step_handler(message, on_click)

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_')) # Обработка ответа админа
def handle_admin_reply(call):
  feedback_id = call.data.split('_')[1]
  msg = bot.send_message(ADMIN_CHAT_ID, f"✍️ Введите ответ на отзыв #{feedback_id}:")
  bot.register_next_step_handler(msg, lambda m: process_admin_reply(m, feedback_id))

def process_admin_reply(message, feedback_id):
  conn = sqlite3.connect(FEEDBACK_DB)
  try:
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, text FROM feedback WHERE id = ?", (feedback_id,)) # Получаем данные отзыва
    feedback_data = cursor.fetchone()
    
    if feedback_data:
      user_id, feedback_text = feedback_data
      
      cursor.execute("UPDATE feedback SET admin_reply = ? WHERE id = ?", (message.text, feedback_id))
      conn.commit() # Обновляем запись в БД
      
      try: # Отправляем ответ пользователю
        bot.send_message(user_id,
          f"📬 <b>Ответ администратора на ваш отзыв:</b>\n\n"
          f"<i>Ваш отзыв:</i>\n<code>{feedback_text}</code>\n\n"
          f"<i>Ответ:</i>\n<code>{message.text}</code>", parse_mode="HTML"
        )
        bot.send_message(ADMIN_CHAT_ID, f"✅ Ответ на отзыв #{feedback_id} отправлен пользователю.")
      except Exception as e:
        bot.send_message(ADMIN_CHAT_ID, f"❌ Не удалось отправить ответ. Пользователь, возможно, заблокировал бота.")
  except Exception as e:
    bot.send_message(ADMIN_CHAT_ID, f"❌ Ошибка при обработке ответа: {e}")
  finally:
    conn.close()

bot.polling(non_stop=True)