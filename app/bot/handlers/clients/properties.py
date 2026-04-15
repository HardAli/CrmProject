from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.clients import (
    get_client_properties_list_keyboard,
    get_client_property_card_keyboard,
    get_property_pick_for_link_keyboard,
    get_relation_status_change_keyboard,
)
from app.common.enums import ClientPropertyRelationStatus
from app.common.formatters.client_property_formatter import (
    format_client_properties_list,
    format_client_property_link_card,
)
from app.services.auth_service import AuthService
from app.services.client_properties import ClientPropertyService

router = Router(name="client_property_links")
DEFAULT_LINKS_LIMIT = 10


@router.callback_query(F.data.startswith("client_properties:"))
async def show_client_properties(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_property_service: ClientPropertyService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_client_id = callback.data.split(":", maxsplit=1)
    if not raw_client_id.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return

    client_id = int(raw_client_id)

    try:
        links = list(
            await client_property_service.get_client_properties(
                current_user=user,
                client_id=client_id,
                limit=DEFAULT_LINKS_LIMIT,
            )
        )
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return

    if not links:
        can_edit = await client_property_service.can_link_properties_to_client(current_user=user, client_id=client_id)
        await callback.message.answer("У клиента пока нет привязанных объектов.")
        await callback.message.answer(
            "Вы можете привязать объект:",
            reply_markup=get_client_properties_list_keyboard(client_id=client_id, links=[], can_edit=can_edit),
        )
        await callback.answer()
        return

    can_edit = client_property_service.can_manage_client_property(
        current_user=user,
        client=links[0].client,
        property_obj=links[0].property,
    )
    await callback.message.answer(
        format_client_properties_list(links=links, client_name=links[0].client.full_name, limit=DEFAULT_LINKS_LIMIT),
        reply_markup=get_client_properties_list_keyboard(client_id=client_id, links=links, can_edit=can_edit),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_property_link_pick:"))
async def pick_property_for_link(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_property_service: ClientPropertyService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_client_id = callback.data.split(":", maxsplit=1)
    if not raw_client_id.isdigit():
        await callback.answer("Некорректный ID клиента", show_alert=True)
        return
    client_id = int(raw_client_id)

    try:
        properties = list(
            await client_property_service.get_available_properties_for_linking(
                current_user=user,
                client_id=client_id,
                limit=DEFAULT_LINKS_LIMIT,
            )
        )
    except ValueError:
        await callback.answer("Клиент не найден или нет прав", show_alert=True)
        return

    if not properties:
        await callback.answer("Нет доступных объектов для привязки", show_alert=True)
        return

    await callback.message.answer(
        "Выберите объект для привязки:",
        reply_markup=get_property_pick_for_link_keyboard(client_id=client_id, properties=properties),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_property_link:"))
async def link_property_to_client(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_property_service: ClientPropertyService,
    session: AsyncSession,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_client_id, raw_property_id = callback.data.split(":", maxsplit=2)
    if not raw_client_id.isdigit() or not raw_property_id.isdigit():
        await callback.answer("Некорректные идентификаторы", show_alert=True)
        return

    client_id = int(raw_client_id)
    property_id = int(raw_property_id)

    existing_link = await client_property_service.get_existing(client_id=client_id, property_id=property_id)
    if existing_link is not None:
        await callback.answer("Этот объект уже привязан к клиенту", show_alert=True)
    else:
        try:
            await client_property_service.link_property_to_client(
                current_user=user,
                client_id=client_id,
                property_id=property_id,
            )
        except ValueError:
            await callback.answer("Клиент или объект недоступен", show_alert=True)
            return
        except PermissionError:
            await callback.answer("Недостаточно прав", show_alert=True)
            return

        await session.commit()
        await callback.answer("Объект привязан")

    links = list(
        await client_property_service.get_client_properties(
            current_user=user,
            client_id=client_id,
            limit=DEFAULT_LINKS_LIMIT,
        )
    )
    can_edit = False
    if links:
        can_edit = client_property_service.can_manage_client_property(
            current_user=user,
            client=links[0].client,
            property_obj=links[0].property,
        )
    if links:
        await callback.message.answer(
            format_client_properties_list(links=links, client_name=links[0].client.full_name, limit=DEFAULT_LINKS_LIMIT),
            reply_markup=get_client_properties_list_keyboard(client_id=client_id, links=links, can_edit=can_edit),
        )


@router.callback_query(F.data.startswith("client_property_view:"))
async def open_link_card(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_property_service: ClientPropertyService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_link_id = callback.data.split(":", maxsplit=1)
    if not raw_link_id.isdigit():
        await callback.answer("Некорректный ID связи", show_alert=True)
        return

    try:
        link = await client_property_service.get_client_property_link(current_user=user, link_id=int(raw_link_id))
    except ValueError:
        await callback.answer("Связь не найдена", show_alert=True)
        return
    except PermissionError:
        await callback.answer("Нет прав на просмотр связи", show_alert=True)
        return

    can_edit = client_property_service.can_manage_client_property(
        current_user=user,
        client=link.client,
        property_obj=link.property,
    )
    await callback.message.answer(
        format_client_property_link_card(link),
        reply_markup=get_client_property_card_keyboard(link_id=link.id, client_id=link.client_id, can_edit=can_edit),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_property_change_status:"))
async def start_relation_status_change(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_property_service: ClientPropertyService,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_link_id = callback.data.split(":", maxsplit=1)
    if not raw_link_id.isdigit():
        await callback.answer("Некорректный ID связи", show_alert=True)
        return

    try:
        link = await client_property_service.get_client_property_link(current_user=user, link_id=int(raw_link_id))
    except (ValueError, PermissionError):
        await callback.answer("Связь недоступна", show_alert=True)
        return

    if not client_property_service.can_manage_client_property(
        current_user=user,
        client=link.client,
        property_obj=link.property,
    ):
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await callback.message.answer(
        "Выберите новый статус связи:",
        reply_markup=get_relation_status_change_keyboard(link_id=link.id, client_id=link.client_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("client_property_set_status:"))
async def set_relation_status(
    callback: CallbackQuery,
    auth_service: AuthService,
    client_property_service: ClientPropertyService,
    session: AsyncSession,
) -> None:
    if callback.message is None:
        await callback.answer()
        return

    user = await auth_service.get_active_user_by_telegram_id(callback.from_user.id)
    if user is None:
        await callback.answer("Нет доступа", show_alert=True)
        return

    _, raw_link_id, raw_status = callback.data.split(":", maxsplit=2)
    if not raw_link_id.isdigit():
        await callback.answer("Некорректный ID связи", show_alert=True)
        return

    try:
        new_status = ClientPropertyRelationStatus(raw_status)
    except ValueError:
        await callback.answer("Некорректный статус", show_alert=True)
        return

    try:
        link = await client_property_service.change_relation_status(
            current_user=user,
            link_id=int(raw_link_id),
            new_status=new_status,
        )
    except ValueError:
        await callback.answer("Связь не найдена", show_alert=True)
        return
    except PermissionError:
        await callback.answer("Недостаточно прав", show_alert=True)
        return

    await session.commit()
    await callback.message.answer(
        format_client_property_link_card(link),
        reply_markup=get_client_property_card_keyboard(link_id=link.id, client_id=link.client_id, can_edit=True),
    )
    await callback.answer("Статус связи обновлён")