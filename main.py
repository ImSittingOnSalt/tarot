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

@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    markup = types.InlineKeyboardMarkup()
    
    # Обработка выбора колоды
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
        
        bot.send_message(
            callback.message.chat.id,
            f'Колода: {deck_name}\nВыбери масть карты:',
            reply_markup=markup
        )
        return
    
    # Разбираем префикс из callback_data
    parts = callback.data.split('_')
    if len(parts) != 2:
        return
    
    prefix, card_type = parts
    
    # Обработка выбора типа карт
    if card_type == 'arc':
        # Старшие арканы
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
        
        bot.edit_message_text(
            "Выберите старший аркан:",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=markup
        )
    
    elif card_type in ['sword', 'wand', 'cup', 'pentacle']:
        # Младшие арканы
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
        
        bot.edit_message_text(
            f"Выберите карту масти {suit_name}:",
            callback.message.chat.id,
            callback.message.message_id,
            reply_markup=markup
        )
    
    # Обработка выбора конкретной карты
    elif any(x in callback.data for x in ['fool', 'magician', 'ace_', 'page_', '2_', '3_']):
        # Здесь будет обработка выбора конкретной карты
        card_name = callback.data.replace(f'{prefix}_', '')
        bot.answer_callback_query(callback.id, f"Выбрана карта: {card_name}")

@bot.message_handler(commands=['daily']) #добавить фото
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

@bot.message_handler(commands=['spreads'])#
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
      ('Справочник таролога 1', 'directory1'),
      ('Справочник таролога 2', 'directory2')
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

@bot.message_handler(commands=['help'])
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

@bot.message_handler(commands=['feedback']) # подробнее потестить ответы(от других людей? мб дело в том, что я сама пишу отзывы и они мне же приходят)
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