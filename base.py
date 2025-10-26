import json
import logging
import os
from datetime import datetime, timedelta

import asyncio
import requests
import aiohttp
from sqlalchemy import update

from database import Session
from models import Receipt, PaidStatusEnum, StatusSudEnum
from sqlalchemy import and_


logger = logging.getLogger(__name__)

class Mixin:
    FOLDER_PATH_BASE = os.getcwd()
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive",
        "Host": "billing.sud.uz",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }


class GetDataDB:
    def __init__(self, user_id, type_of_receipt):
        self.user_id = user_id
        self.type_of_receipt = type_of_receipt

    def get_correct_amount(self, sum):
        percent_of_summ = sum * (4 / 100)
        if percent_of_summ < 375000:
            percent_of_summ = 375000
        return percent_of_summ

    def get_data_from_db_to_create_receipts(self):
        session = Session()
        rows = session.query(Receipt).filter_by(status_of_created=False,
                                                type_of_sud=self.type_of_receipt,
                                                paid=PaidStatusEnum.NOT_CREATED,
                                                user_id=self.user_id).all()
        session.close()

        _dict = {}
        for row in rows:
            if self.type_of_receipt == StatusSudEnum.CIVIL:
                sum_of_debt = self.get_correct_amount(row.sum_of_debt)
            else:
                sum_of_debt = row.sum_of_debt

            _dict[f'{row.id}'] = {
                'fio': row.fio,
                'name_of_region': row.name_of_region,
                'id_sud': row.id_sud,
                'name_of_client': row.name_of_client,
                'stir_of_client': row.stir_of_client,
                'sum_of_debt': sum_of_debt,
                'pinfl_of_debtor': row.pinfl_of_debtor,
                'address_of_client': row.address_of_client,
            }

        return _dict

    def get_data_from_db_for_download_pdf_today(self, ids, check=False):
        session = Session()
        _filter = [
            Receipt.type_of_sud == self.type_of_receipt,
            Receipt.user_id == self.user_id,
            Receipt.id.in_(ids)
        ]
        if not check:
            _filter.append(Receipt.paid == PaidStatusEnum.PAID)
        rows = session.query(Receipt).filter(
            and_(
                *_filter
            )
        ).all()
        session.close()

        data = []
        if check:
            for row in rows:
                data.append((row.fio, row.paid, row.pinfl_of_debtor, row.number_of_receipt))
        else:
            for row in rows:
                data.append((row.fio, row.pinfl_of_debtor, row.number_of_receipt))
        return data


def read_files_in_folder(folder_path, id):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.json'):
            file_path = os.path.join(folder_path, file_name)
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for obj in data:
                    if obj['id'] == id:
                        return obj['name']


class CheckPaidReceipt(Mixin):
    def __init__(self, user_id, type_of_sud, ids=None, is_self_paid=False):
        self.type_of_sud = type_of_sud
        self.user_id = user_id
        self.ids = None
        if ids is not None:
            self.ids = ids
        self.is_self_paid = is_self_paid

    def get_receipts_to_check_paid(self):
        session = Session()
        filter_list = [
            Receipt.status_of_created == True,
            Receipt.type_of_sud == self.type_of_sud,
            Receipt.paid.in_([PaidStatusEnum.CHECKING, PaidStatusEnum.CREATED]),
            Receipt.user_id == self.user_id,
        ]
        if self.ids is not None:
            filter_list.append(Receipt.id.in_(self.ids))
        rows = session.query(Receipt).filter(
            and_(
                *filter_list
            )
        ).all()
        session.close()

        data = []
        for row in rows:
            data.append((row.id, row.number_of_receipt))

        return data

    async def _request(self, data, headers, session, results):
        url = f"https://***/api/invoice/checkStatus?invoice={data[1]}&lang=ruName"
        _receipt_update = {'id': data[0], 'paid': None}
        if self.is_self_paid:
            _receipt_update['receipt_paid_at'] = datetime.now()
        try:
            async with session.get(url, headers=headers, timeout=120) as response:
                response.raise_for_status()

                if response.status == 200:
                    response_data = await response.json()
                    if response_data.get('invoiceStatus') == 'PAID':
                        logger.info(f"Квитанция {response_data.get('number')} оплачена")
                        _receipt_update['paid'] = 'PAID'
                        results.append(_receipt_update)
                    elif response_data.get('invoiceStatus') == 'CHECKING':
                        logger.info(f"Квитанция {response_data.get('number')} проверяется")
                        _receipt_update['paid'] = 'CHECKING'
                        results.append(_receipt_update)
                    else:
                        logger.error(f'Для квитанции - {data[1]}, статус оплаты не изменился.')

        except Exception as e:
            logger.error(f"Не удалось проверить квитанцию,\nОшибка: {e}",
                         extra={"user_message": f'Квитанция {data[1]} не была проверена, подключение с ошибкой.'})

    async def api_request_to_check_receipt(self, data):
        headers = self.HEADERS.copy()
        results = []
        tasks = []
        data_blocks = [data[i:i + 20] for i in range(0, len(data), 20)]
        async with aiohttp.ClientSession() as session:
            for block in data_blocks:
                tasks.extend(
                    [self._request(_data, headers, session, results) for _data in block]
                )
                await asyncio.gather(*tasks)

                if results:
                    self._update_paid_receipts_in_db(results)

                results.clear()
                tasks.clear()

    def _update_paid_receipts_in_db(self, results):
        session = Session()
        try:
            session.execute(
                update(Receipt),
                results
            )
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка обновления квитанций: {e}",
                         extra={"user_message": "Ошибка при обновлении квитанций в БД"})
        finally:
            session.close()

    def process(self):
        data_receipts_to_check = self.get_receipts_to_check_paid()
        if not data_receipts_to_check:
            logger.info(f'Данные для проверки не найдены.')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.api_request_to_check_receipt(data_receipts_to_check))


def run_check_paid_receipt(user_id, type_of_receipt, ids=None, is_self_paid=False):
    CheckPaidReceipt(user_id, type_of_receipt, ids=ids, is_self_paid=is_self_paid).process()
