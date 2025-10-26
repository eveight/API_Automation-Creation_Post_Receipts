import logging

import pandas as pd
from database import Session
from models import Receipt, PaidStatusEnum
from sqlalchemy.exc import SQLAlchemyError
from models import Receipt

from validators.excel_validators import validate_receipt

from config.modal_log_handler import ModalLogHandler

logger = logging.getLogger(__name__)


def parse_excel_data_civil_receipts(file_path, user_id, type_of_receipt, modal_window):
    try:
        modal_handler = ModalLogHandler()
        modal_handler.set_modal_window(modal_window)
        logger.addHandler(modal_handler)

        df = pd.read_excel(file_path, sheet_name='Основной борд', header=0)

        validate_receipt(df)

        rows_list = df.values.tolist()
    except Exception as e:
        logger.error(f"Ошибка во время чтения эксель файла: {e}",
                     extra={"user_message": f"Ошибка при чтения эксель файла"})
        raise e

    error = None
    session = Session()
    try:
        with (session.begin()):
            for idx, row in enumerate(rows_list):
                sum_of_debt = row[6]
                try:
                    existing_receipt = session.query(Receipt).filter(Receipt.pinfl_of_debtor == str(row[7]),
                                                                     Receipt.type_of_sud == type_of_receipt,
                                                                     Receipt.user_id == user_id,
                                                                     ).with_for_update().first()
                except SQLAlchemyError as e:
                    logger.error(f"Ошибка запроса в БД: {e}",
                                 extra={"user_message": f"Ошибка загрузки данных в БД"})
                    session.rollback()
                    raise e

                if existing_receipt:
                    if existing_receipt.paid == PaidStatusEnum.PAID:
                        logger.info(f"Квитанция № {existing_receipt.number_of_receipt} уже оплачена")
                        continue
                    elif existing_receipt.status_of_created and existing_receipt.paid == PaidStatusEnum.CREATED:
                        logger.info(f"Квитанция № {existing_receipt.number_of_receipt} уже создана но еще не оплачена")
                        continue
                    else:
                        existing_receipt.name_of_region = row[1]
                        existing_receipt.id_sud = row[2]
                        existing_receipt.name_of_client = row[3]
                        existing_receipt.stir_of_client = row[4]
                        existing_receipt.fio = row[5]
                        existing_receipt.sum_of_debt = sum_of_debt
                        existing_receipt.address_of_client = row[9]
                        existing_receipt.status_of_created = False
                        existing_receipt.paid = PaidStatusEnum.NOT_CREATED
                else:
                    receipt_civil = Receipt(
                        name_of_region=row[1],
                        id_sud=row[2],
                        name_of_client=row[3],
                        stir_of_client=row[4],
                        fio=row[5],
                        sum_of_debt=sum_of_debt,
                        pinfl_of_debtor=str(row[7]),
                        address_of_client=row[9],
                        type_of_sud=type_of_receipt,
                        status_of_created=False,
                        paid=PaidStatusEnum.NOT_CREATED,
                        user_id=user_id
                    )
                    session.add(receipt_civil)
        session.commit()
        logger.info("Данные успешно загружены в БД")
    except SQLAlchemyError as e:
        logger.error(f"Ошибка сохранения данных в БД,\nОшибка: {e}",
                     extra={"user_message": f"Ошибка загрузки данных в БД"})
        session.rollback()
        error = e
    finally:
        logger.removeHandler(modal_handler)
        session.close()
        if error is not None:
            raise error
