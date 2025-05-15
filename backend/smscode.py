@router.message(lambda message: message.text == "По Номеру")
async def get_number_tg(message: types.Message, state: FSMContext) -> None:
    user_departments = await FILE_SERVICE.get_user_departments(message.from_user.id)
    if not user_departments:
        await message.answer("Вы не зарегистрированы. Обратитесь к администратору.")
        return
    user_id = message.from_user.id
    preferred_departments = ["C2", "T", "T2", "Poltava", "Alex", "Kabany", "Training_center"]
    department_name = None
    for dept in preferred_departments:
        if dept in user_departments:
            department_name = dept
            break
    if not department_name:
        department_name = next(iter(user_departments), "Unknown")
    numbertg_folder = os.path.join(NUMBER_TG_FOLDER, department_name)
    folder_type = "number_tg"
    try:
        dirs = [d for d in os.listdir(numbertg_folder) if (Path(numbertg_folder) / d).is_dir()]
        if not dirs:
            await message.answer("Нет доступных аккаунтов по номеру.")
            return
    except FileNotFoundError:
        logging.error(f"Папка '{numbertg_folder}' не найдена.")
        await message.answer(f"Папка {numbertg_folder} не найдена.")
        return
    rand_dir = random.choice(dirs)
    folder_path = os.path.join(numbertg_folder, rand_dir)
    json_file_path = os.path.join(folder_path, f"{rand_dir}.json")
    if not os.path.exists(json_file_path):
        await message.answer("Номер бракованный, возьмите другой.")
        await FILE_SERVICE._move_to_tg_old(folder_path, department_name, "session")
        return
    try:
        async with aiofiles.open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.loads(await file.read())
    except Exception as e:
        logging.error(f"Ошибка чтения {json_file_path}: {e}")
        await message.answer("Ошибка при чтении данных аккаунта. Номер бракованный, возьмите другой.")
        await FILE_SERVICE._move_to_tg_old(folder_path, department_name, "session")
        return
    required_keys = ["app_id", "app_hash", "phone", "device"]
    missing_keys = [k for k in required_keys if k not in data]
    if missing_keys:
        await message.answer(
            f"Отсутствуют обязательные поля {', '.join(missing_keys)}. Номер бракованный, возьмите другой."
        )
        await FILE_SERVICE._move_to_tg_old(folder_path, department_name, "session")
        return
    twoFa = data.get("twoFa") or data.get("twoFA") or ""
    api_id = data['app_id']
    api_hash = data['app_hash']
    phone = data.get('phone')
    if not phone:
        await message.answer("Ошибка: номер телефона отсутствует в данных. Номер бракованный, возьмите другой.")
        await FILE_SERVICE._move_to_tg_old(folder_path, department_name, "session")
        return
    device_model = data['device']
    system_version = data.get('system_version', "unknown")
    app_version = data.get('app_version', "4.11.5 x64")
    await message.answer(f"Вот номер для входа: {phone.split('.')[0]}")
    if twoFa:
        await message.answer(f"twoFA: {twoFa.split('.')[0]}")
    session_file = os.path.join(folder_path, f"{rand_dir}.session")
    proxy_tuple = None
    proxies_file = "proxies.txt"
    if os.path.exists(proxies_file):
        try:
            async with aiofiles.open(proxies_file, "r", encoding="utf-8") as f:
                proxies_data = await f.read()
            proxy_lines = [line.strip() for line in proxies_data.splitlines() if line.strip()]
            valid_proxies = []
            for line in proxy_lines:
                parts = line.split(":")
                if len(parts) == 4:
                    valid_proxies.append(line)
            attempts = 0
            while valid_proxies and attempts < len(valid_proxies):
                selected_proxy = random.choice(valid_proxies)
                parts = selected_proxy.split(":")
                candidate = auto_detect_proxy(parts[0], parts[1], parts[2], parts[3])
                if candidate:
                    if await test_proxy(candidate):
                        proxy_tuple = candidate
                        logging.info(f"Используем прокси: {parts[0]}:{parts[1]} с протоколом {candidate[0]}")
                        break
                    else:
                        logging.info(f"Прокси {parts[0]}:{parts[1]} не прошёл проверку.")
                else:
                    logging.info(f"Прокси {parts[0]}:{parts[1]} не удалось определить тип.")
                valid_proxies.remove(selected_proxy)
                attempts += 1
        except Exception as e:
            logging.error(f"Ошибка при получении или проверке прокси из файла: {e}")
    from telethon import TelegramClient
    client = TelegramClient(
        session_file,
        api_id,
        api_hash,
        proxy=proxy_tuple,
        device_model=device_model,
        system_version=system_version,
        app_version=app_version,
        system_lang_code="en-GB",
        lang_code="en"
    )
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await asyncio.sleep(25)
            token = str(uuid.uuid4())
            TEMP_CLIENTS[message.from_user.id] = {
                "client": client,
                "folder_path": folder_path,
                "department_name": department_name,
                "rand_dir": rand_dir,
                "folder_type": folder_type,
                "token": token
            }
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            inline_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("Ожидайте код...", callback_data="wait")]
            ])
            sent_msg = await message.answer("Запрос кода отправлен. Ожидайте поступления кода...", reply_markup=inline_kb)
            asyncio.create_task(wait_for_code_and_update(client, message, sent_msg, token, FILE_SERVICE))
            return
        else:
            await message.answer("Ожидаю код авторизации.")
            await asyncio.sleep(25)
            async for msg777 in client.iter_messages(777000, limit=1):
                msg_text = msg777.text
                if msg_text:
                    await message.answer(msg_text.split('.')[0])
                else:
                    await message.answer("Не удалось получить сообщение от 777000.")
            await FILE_SERVICE.log_number_tg_access(
                user_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                folder_type=folder_type,
                folder_name=rand_dir,
                department=department_name
            )
    except Exception as e:
        logging.error(f"Ошибка при работе с телегой {rand_dir}: {e}")
        await message.answer("Произошла ошибка. Попробуйте другой номер.")
    finally:
        try:
            if message.from_user.id not in TEMP_CLIENTS:
                await client.disconnect()
        except Exception:
            pass
    if message.from_user.id not in TEMP_CLIENTS:
        await FILE_SERVICE._move_to_tg_old(folder_path, department_name, "session")