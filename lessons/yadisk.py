import asyncio
import urllib.parse

import aiohttp

API_HOST = 'https://cloud-api.yandex.net/'
API_VERSION = 'v1'
REQUEST_UPLOAD_URL = f'{API_HOST}{API_VERSION}/disk/resources/upload'
DOWNLOAD_LINK_URL = f'{API_HOST}{API_VERSION}/disk/resources/download'


async def _upload_one(session, filename, file_bytes, token):
    headers = {'Authorization': f'OAuth {token}'}
    path = f'app:/{filename}'

    # 1. Получаем URL для загрузки
    async with session.get(
        REQUEST_UPLOAD_URL,
        headers=headers,
        params={'path': path, 'overwrite': 'True'},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()
    upload_url = data['href']

    # 2. PUT файл (без Authorization — как в теории YaCut)
    async with session.put(upload_url, data=file_bytes) as resp:
        resp.raise_for_status()
        # Яндекс Диск возвращает путь вида "disk:/app/filename"
        # Для шага 3 используем тот же path, что передавали в шаге 1
        location = path

    # 3. Ссылка на скачивание
    async with session.get(
        DOWNLOAD_LINK_URL,
        headers=headers,
        params={'path': location},
    ) as resp:
        resp.raise_for_status()
        data = await resp.json()

    return data['href']


async def _upload_many(files_data, token):
    async with aiohttp.ClientSession() as session:
        tasks = [
            _upload_one(session, name, data, token)
            for name, data in files_data
        ]
        urls = await asyncio.gather(*tasks)
    return list(zip([name for name, _ in files_data], urls))


def upload_to_yadisk(filename, file_bytes, token):
    """Синхронная обёртка для вызова из api/serializers.py.
    Возвращает (filename, download_url).
    """
    try:
        result = asyncio.run(_upload_many([(filename, file_bytes)], token))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(
                _upload_many([(filename, file_bytes)], token)
            )
        finally:
            loop.close()
    return result[0]  # (filename, download_url)
