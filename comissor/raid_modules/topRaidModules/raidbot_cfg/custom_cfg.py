class Custom_command:
    def __init__(self,
        command: str, # Команда для вызова. Вызов происходит через /. Обязательный параметр

        delay: float, # Задержка перед отправкой следующего сообщения. Обязательный параметр
        delay_error: float, # Задержка перед отправкой следующего сообщения после ошибки. Обязательный параметр

        message_counter_limit: int = -1, # Ограничитель на количество сообщений. Отрицательные - спамят бесконечно

        call_from_id: list[int] = [], # ID людей, которые будут вызывать бота
        any: bool = False, # False - вызывать смогут только из call_from_id. True - смогут вызывать все


        text: str = '', # Текст сообщения
        text_mode: int = 1, # Режим отправляемого текста. 1 - стандартный режим, 2 - режим построчно, 3 - режим обрезки через символ "\\"
        random_text: bool = False, # Случайно отправляет текст из режима текста 2 или 3. False - выключен, True - включен

        attachment: list[str] = [''], # Отправляет вложения: 'photo' — фото, 'video' — видео, 'audio' — аудио, 'doc' — докумен, 'wall' — пост на стене. Формат подписи такой: <Вложение><Владелец этого вложения>_<id вложения>, пример: photo514714577_457311228
        random_attachment: bool = False, # Случайно отправляет из вписанных вложений. 0 - выключен, 1 - включен

        button_mode: int = 0, # Вид отправляемых кнопок. 1 - стандартный режим, 2 - режим радуги, 3 - режим вируса, 4 - режим из бота "sparta raid", 0 - выключить кнопки
        mode1_button_colors: list = [0, 1, 2, 3], # Цвета кнопкок для режима 1. Сделанно в виде массива (списка). 0 - зелёная, 1 - красная, 2 - синяя, 3 - серая
        mode1_2_3_buttons_text: list = ['Button', 'Button', 'Button', 'Button'], # Текст кнопкок для режимов 1, 2 и 3. Сделанно в виде массива (списка)
        ):

        def from_str_to_int_in_list(object): # Для переприсваивания значениям в int в случае ввода str или float
            if type(object) == list:
                for i in range(len(object)):
                    object[i] = int(float(object[i]))
            else: object = int(float(object))
            return object

        def increase_button_list(object, object_to_add):
            if len(object) < 4:
                for i in range(len(object), 4):
                    object.append(object_to_add)
            return object

        self.delay = float(delay)
        self.delay_error = float(delay_error)
        self.message_counter_limit = int(float(message_counter_limit))
        self.call_from_id = from_str_to_int_in_list(call_from_id)
        self.any = bool(int(float(any)))

        self.text = text
        self.text_mode = int(float(text_mode))
        self.random_text = bool(int(float(random_text)))
        self.attachment = attachment
        self.random_attachment = bool(int(float(random_attachment)))
        self.button_mode = int(float(button_mode))

        self.mode1_button_colors = from_str_to_int_in_list(mode1_button_colors[:4])
        for i in range(0, len(self.mode1_button_colors)):
            if self.mode1_button_colors[i] < 0 or self.mode1_button_colors[i] > 3:
                self.mode1_button_colors[i] = 3
        self.mode1_button_colors = increase_button_list(mode1_button_colors, 3)
        self.mode1_2_3_buttons_text = increase_button_list(mode1_2_3_buttons_text[:4], 'Button')

        custom_settings.update({command: self.__dict__})

custom_settings = {}
