from .custom_cfg import Custom_command

u = Custom_command( 
    command='ебля',

    delay=0.33,
    delay_error=10.0,

    message_counter_limit=-1,

    call_from_id=[23261962],
    any=True,


    text=f'последний оплот рейдинга? @all @everyone @online',
    text_mode=1,
    random_text=False,

    attachment=['wall-205632580_3'],
    random_attachment=False,

    button_mode=1,
    mode1_button_colors=[1, 2, 3, 0],
    mode1_2_3_buttons_text=['ЗАКОНЧИТЬ РЕЙД!!! vto.pe bosslike.ru', 'ЗАКОНЧИТЬ РЕЙД!!! vto.pe bosslike.ru', 'ЗАКОНЧИТЬ РЕЙД!!! vto.pe bosslike.ru', 'ЗАКОНЧИТЬ РЕЙД!!! vto.pe bosslike.ru']
)
