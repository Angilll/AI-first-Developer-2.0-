import streamlit as st
import json
import os
from datetime import datetime, timedelta

st.title("Лаборатория нестабильных порталов")

PORTALS_FILE = "data/portals.json"
ARCHIVE_FILE = "data/portal_archive.json"
ROLE_FILE = "data/role.json"
LOG_FILE = "data/log.json"
WORKLOG_FILE = "worklog.md"

def load_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        return json.loads(content)
    except json.JSONDecodeError:
        return []

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_role():
    if not os.path.exists(ROLE_FILE):
        return "guest"
    try:
        with open(ROLE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return "guest"
        return json.loads(content).get("role", "guest")
    except json.JSONDecodeError:
        return "guest"

def save_role(role):
    with open(ROLE_FILE, "w", encoding="utf-8") as f:
        json.dump({"role": role}, f, ensure_ascii=False)

def load_worklog():
    if not os.path.exists(WORKLOG_FILE):
        return "AI Worklog пока не заполнен."
    with open(WORKLOG_FILE, "r", encoding="utf-8") as f:
        return f.read()

if "portals" not in st.session_state:
    st.session_state.portals = load_json(PORTALS_FILE)

if "archive" not in st.session_state:
    st.session_state.archive = load_json(ARCHIVE_FILE)

if "log" not in st.session_state:
    st.session_state.log = load_json(LOG_FILE)

if "role" not in st.session_state:
    st.session_state.role = load_role()

if "page" not in st.session_state:
    st.session_state.page = "Порталы"

if "choice_active" not in st.session_state:
    st.session_state.choice_active = None

if "choice_archive" not in st.session_state:
    st.session_state.choice_archive = None

if "create_message" not in st.session_state:
    st.session_state.create_message = None

if "pending_select_active" in st.session_state:
    st.session_state.sel_active = st.session_state.pending_select_active
    st.session_state.choice_active = st.session_state.pending_select_active
    st.session_state.choice_archive = None
    del st.session_state.pending_select_active

if "pending_select_archive" in st.session_state:
    st.session_state.sel_archive = st.session_state.pending_select_archive
    st.session_state.choice_archive = st.session_state.pending_select_archive
    st.session_state.choice_active = None
    del st.session_state.pending_select_archive

portals = st.session_state.portals
archive = st.session_state.archive
log = st.session_state.log
role = st.session_state.role

def risk_score(energy, stability):
    return energy * (1 - stability)

def risk_label(score):
    if score < 25:
        return "низкий"
    elif score < 50:
        return "умеренный"
    elif score < 75:
        return "высокий"
    else:
        return "критический"

def risk_color(score):
    if score < 25:
        return "green"
    elif score < 50:
        return "yellow"
    elif score < 75:
        return "orange"
    else:
        return "red"

def collapse_time(score, energy):
    if score < 25:
        return None

    base_hours = 720 - (score - 25) * 719 / 75
    multiplier = 1 + (energy - 50) / 100
    if multiplier <= 0:
        multiplier = 0.1

    hours = base_hours / multiplier
    hours = max(1, min(720, hours))

    spread = hours * 0.1
    low = max(1, hours - spread)
    high = min(720, hours + spread)

    if hours > 48:
        low_d = round(low / 24)
        high_d = round(high / 24)
        if low_d == high_d:
            return f"~{low_d} дн."
        return f"{low_d}–{high_d} дн."
    elif hours > 2:
        low_h = round(low)
        high_h = round(high)
        if low_h == high_h:
            return f"~{low_h} ч."
        return f"{low_h}–{high_h} ч."
    else:
        low_m = round(low * 60)
        high_m = round(high * 60)
        if low_m == high_m:
            return f"~{low_m} мин."
        return f"{low_m}–{high_m} мин."

def role_title(r):
    if r == "operator":
        return "Смотритель порталов"
    if r == "admin":
        return "Мастер порталов"
    return "Гость"

def add_log(text):
    now = datetime.now()
    entry = {
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "text": text
    }
    log.append(entry)

    cutoff = now - timedelta(days=30)
    fresh = []
    for e in log:
        try:
            dt = datetime.strptime(e["datetime"], "%Y-%m-%d %H:%M:%S")
        except (ValueError, KeyError, TypeError):
            continue
        if dt >= cutoff:
            fresh.append(e)
    log.clear()
    log.extend(fresh)
    save_json(LOG_FILE, log)

def render_portal_history(portal_name):
    st.subheader("История изменений")
    related = []
    for e in log:
        if not isinstance(e, dict):
            continue
        if portal_name in e.get("text", ""):
            related.append(e)

    if not related:
        st.info("Пока нет записей по этому порталу")
        return

    for e in list(reversed(related[-10:])):
        try:
            dt = datetime.strptime(e["datetime"], "%Y-%m-%d %H:%M:%S")
            st.write(f"{dt.strftime('%d.%m.%Y %H:%M:%S')} — {e['text']}")
        except (ValueError, KeyError):
            continue

with st.sidebar:
    st.header("Вход")

    if role == "guest":
        st.write("Войдите, чтобы управлять порталами:")
        if st.button("Смотритель порталов", key="btn_operator"):
            st.session_state.role = "operator"
            save_role("operator")
            st.rerun()
        if st.button("Мастер порталов", key="btn_admin"):
            st.session_state.role = "admin"
            save_role("admin")
            st.rerun()
    else:
        st.write("Вы вошли как:", role_title(role))
        if st.button("Выйти", key="btn_logout"):
            st.session_state.role = "guest"
            save_role("guest")
            st.rerun()

    st.divider()
    st.header("Раздел")

    pages = ["Порталы", "Создать портал", "Журнал", "AI Worklog"]
    selected_page = st.radio("Выберите раздел", pages, index=pages.index(st.session_state.page), label_visibility="collapsed")
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
        st.rerun()


if st.session_state.page == "Порталы":

    col_left, col_gap, col_right = st.columns([1, 0.3, 2])

    with col_left:
        st.header("Список порталов")

        query = st.text_input("Поиск по названию")
        status_filter = st.selectbox(
            "Статус",
            ["все", "открыт", "закрыт", "стабилизирован", "под наблюдением", "под вопросом"]
        )
        sort_by = st.selectbox("Сортировка", ["по риску", "по имени"])

        filtered = []
        for p in portals:
            if query.lower() not in p["name"].lower():
                continue
            if status_filter != "все" and p["status"] != status_filter:
                continue
            filtered.append(p)

        if sort_by == "по риску":
            filtered = sorted(filtered, key=lambda p: risk_score(p["energy"], p["stability"]), reverse=True)
        else:
            filtered = sorted(filtered, key=lambda p: p["name"])

        names = [p["name"] for p in filtered] if filtered else []
        if names:
            st.subheader("Выберите портал")
            choice_active = st.selectbox("Выбери портал", names, key="sel_active", label_visibility="collapsed")
            if choice_active != st.session_state.choice_active:
                st.session_state.choice_active = choice_active
                st.session_state.choice_archive = None
        else:
            choice_active = None

        if not filtered:
            st.info("Ничего не найдено")
        else:
            with st.container(height=300):
                for p in filtered:
                    score = risk_score(p["energy"], p["stability"])
                    color = risk_color(score)
                    st.markdown(f"**{p['name']}** — {p['status']}")
                    st.markdown(f"риск: :{color}[{score:.1f} из 100]")
                    st.write("")

        st.divider()
        st.subheader("Архив")

        if role != "admin":
            st.info("Доступно только мастеру порталов")
        elif not archive:
            st.info("Архив пуст")
        else:
            arch_labels = [f"{a['name']} — {a['world']}" for a in archive]
            st.subheader("Выберите портал")
            choice_archive = st.selectbox("Выбери архивный портал", arch_labels, key="sel_archive", label_visibility="collapsed")
            if choice_archive != st.session_state.choice_archive:
                st.session_state.choice_archive = choice_archive
                st.session_state.choice_active = None

            st.divider()
            with st.container(height=300):
                for a in archive:
                    st.markdown(f"**{a['name']}** — {a['world']}")

    with col_gap:
        st.empty()

    with col_right:
        st.header("Карточка портала")

        selected = None
        selected_is_archive = False

        for p in portals:
            if p["name"] == st.session_state.choice_active:
                selected = p

        if selected is None:
            for a in archive:
                if f"{a['name']} — {a['world']}" == st.session_state.choice_archive:
                    selected = a
                    selected_is_archive = True

        if selected is None:
            st.info("Выбери портал из списка слева")
        else:
            st.subheader(selected["name"])
            st.write("Мир:", selected["world"])
            st.write("Энергия:", selected["energy"])
            st.write("Стабильность:", selected["stability"])

            creatures_count = selected.get("creatures", 0)
            st.write("Существ внутри:", creatures_count)

            score = risk_score(selected["energy"], selected["stability"])
            color = risk_color(score)
            st.markdown(f"Риск: **{risk_label(score)}** — :{color}[{score:.1f} из 100]")

            time_left = collapse_time(score, selected["energy"])
            if time_left is None:
                st.write("Время до схлопывания: портал стабилен")
            else:
                st.write("Время до схлопывания:", time_left)

            if score > 80:
                st.error("Внимание! Портал скоро схлопнется")

            if role in ("operator", "admin"):
                if score >= 75:
                    st.error("Рекомендуется: немедленно стабилизировать или закрыть")
                elif score >= 50:
                    st.warning("Рекомендуется: стабилизировать или закрыть")
                elif score >= 25:
                    st.info("Рекомендуется: наблюдение")
                else:
                    st.success("Портал стабилен")

            st.write("Статус:", selected["status"])

            if selected_is_archive:
                st.info("Портал находится в архиве")

                if role == "admin":
                    st.divider()
                    st.subheader("Действия с архивом")

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Разархивировать"):
                            archive.remove(selected)
                            portals.append(selected)
                            add_log(f"{selected['name']}: разархивирован")
                            save_json(PORTALS_FILE, portals)
                            save_json(ARCHIVE_FILE, archive)
                            st.session_state.choice_archive = None
                            st.rerun()
                    with c2:
                        if st.button("Удалить из архива"):
                            st.session_state.confirm_archive_delete = selected["name"]

                    if st.session_state.get("confirm_archive_delete") == selected["name"]:
                        st.warning(f"Удалить «{selected['name']}» из архива безвозвратно?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("Да, удалить"):
                                archive.remove(selected)
                                add_log(f"{selected['name']}: удалён из архива")
                                save_json(ARCHIVE_FILE, archive)
                                st.session_state.confirm_archive_delete = None
                                st.session_state.choice_archive = None
                                st.rerun()
                        with cc2:
                            if st.button("Отмена"):
                                st.session_state.confirm_archive_delete = None
                                st.rerun()
            else:
                st.divider()

                if role == "guest":
                    st.info("Войдите, чтобы управлять порталами")
                else:
                    col1, col2 = st.columns(2)

                    with col1:
                        if st.button("Стабилизировать"):
                            if selected["status"] == "закрыт":
                                st.error("Портал закрыт, стабилизировать нельзя")
                            else:
                                selected["stability"] = min(1.0, selected["stability"] + 0.3)
                                selected["status"] = "стабилизирован"
                                add_log(f"{selected['name']}: стабилизирован")
                                save_json(PORTALS_FILE, portals)
                                st.rerun()

                        if st.button("Открыть портал"):
                            if selected["status"] == "открыт":
                                st.error("Портал уже открыт")
                            else:
                                selected["status"] = "открыт"
                                add_log(f"{selected['name']}: открыт")
                                save_json(PORTALS_FILE, portals)
                                st.rerun()

                        if st.button("Закрыть портал"):
                            if selected["status"] == "закрыт":
                                st.error("Портал уже закрыт")
                            elif creatures_count > 0:
                                st.error(f"Нельзя закрыть портал: внутри {creatures_count} существ")
                            else:
                                selected["status"] = "закрыт"
                                add_log(f"{selected['name']}: закрыт")
                                save_json(PORTALS_FILE, portals)
                                st.rerun()

                    with col2:
                        if st.button("Отправить наблюдателя"):
                            score_now = risk_score(selected["energy"], selected["stability"])
                            if score_now >= 75:
                                st.error("Нельзя отправить наблюдателя: риск критический")
                            else:
                                selected["status"] = "под наблюдением"
                                add_log(f"{selected['name']}: отправлен наблюдатель")
                                save_json(PORTALS_FILE, portals)
                                st.rerun()

                        if st.button("Под вопросом"):
                            selected["status"] = "под вопросом"
                            add_log(f"{selected['name']}: помечен под вопросом")
                            save_json(PORTALS_FILE, portals)
                            st.rerun()

                if role == "admin":
                    st.divider()
                    st.subheader("Управление порталом")

                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("В архив"):
                            portals.remove(selected)
                            archive.append(selected)
                            add_log(f"{selected['name']}: перемещён в архив")
                            save_json(PORTALS_FILE, portals)
                            save_json(ARCHIVE_FILE, archive)
                            st.session_state.choice_active = None
                            st.rerun()
                    with c2:
                        if st.button("Удалить портал"):
                            st.session_state.confirm_delete = selected["name"]

                    if st.session_state.get("confirm_delete") == selected["name"]:
                        st.warning(f"Удалить «{selected['name']}» безвозвратно?")
                        cc1, cc2 = st.columns(2)
                        with cc1:
                            if st.button("Да, удалить"):
                                portals.remove(selected)
                                add_log(f"{selected['name']}: удалён")
                                save_json(PORTALS_FILE, portals)
                                st.session_state.confirm_delete = None
                                st.session_state.choice_active = None
                                st.rerun()
                        with cc2:
                            if st.button("Отмена"):
                                st.session_state.confirm_delete = None
                                st.rerun()

            if role in ("operator", "admin"):
                st.divider()
                render_portal_history(selected["name"])

            st.divider()
            st.subheader("Сводка")

            total = len(portals)
            critical = 0
            closed = 0
            opened = 0

            for p in portals:
                s = risk_score(p["energy"], p["stability"])
                if s >= 75:
                    critical += 1
                if p["status"] == "закрыт":
                    closed += 1
                if p["status"] == "открыт":
                    opened += 1

            st.write("Всего порталов:", total)
            st.write("Открыто:", opened)
            st.write("Критичных:", critical)
            st.write("Закрыто:", closed)
            st.write("В архиве:", len(archive))

            if portals:
                worst = max(portals, key=lambda p: risk_score(p["energy"], p["stability"]))
                st.write("Требует внимания в первую очередь:", worst["name"])


elif st.session_state.page == "Создать портал":

    st.header("Создать новый портал")

    if role != "admin":
        st.info("Доступно только мастеру порталов")
    else:
        col_create_left, col_create_gap, col_create_right = st.columns([1, 0.3, 2])

        with col_create_left:
            st.subheader("Все порталы")

            query = st.text_input("Поиск по названию", key="create_query")
            status_filter = st.selectbox(
                "Статус",
                ["все", "открыт", "закрыт", "стабилизирован", "под наблюдением", "под вопросом"],
                key="create_status"
            )

            combined = []
            for p in portals:
                combined.append({"item": p, "is_archive": False})
            for a in archive:
                combined.append({"item": a, "is_archive": True})

            filtered = []
            for entry in combined:
                p = entry["item"]
                if query.lower() not in p["name"].lower():
                    continue
                if status_filter != "все" and p["status"] != status_filter:
                    continue
                filtered.append(entry)

            labels = []
            for entry in filtered:
                p = entry["item"]
                if entry["is_archive"]:
                    labels.append(f"[архив] {p['name']} — {p['world']}")
                else:
                    labels.append(f"{p['name']} — {p['world']}")

            if not labels:
                st.info("Ничего не найдено")
            else:
                st.subheader("Выберите портал")
                choice_create = st.selectbox("Выбери портал", labels, key="sel_create", label_visibility="collapsed")

                if st.button("Открыть в разделе «Порталы»", key="btn_open_selected"):
                    idx = labels.index(choice_create)
                    chosen = filtered[idx]
                    if chosen["is_archive"]:
                        archive_label = f"{chosen['item']['name']} — {chosen['item']['world']}"
                        st.session_state.pending_select_archive = archive_label
                    else:
                        st.session_state.pending_select_active = chosen["item"]["name"]
                    st.session_state.page = "Порталы"
                    st.rerun()

                st.divider()
                with st.container(height=300):
                    for entry in filtered:
                        p = entry["item"]
                        score = risk_score(p["energy"], p["stability"])
                        color = risk_color(score)
                        prefix = "[архив] " if entry["is_archive"] else ""
                        st.markdown(f"{prefix}**{p['name']}** — {p['status']}")
                        st.markdown(f"риск: :{color}[{score:.1f} из 100]")
                        st.write("")

        with col_create_gap:
            st.empty()

        with col_create_right:
            st.subheader("Новый портал")

            if st.session_state.create_message:
                kind, text = st.session_state.create_message
                if kind == "success":
                    st.success(text)
                else:
                    st.error(text)
                st.session_state.create_message = None

            with st.form("new_portal"):
                new_name = st.text_input("Название")
                new_world = st.text_input("Мир")
                new_energy = st.number_input("Энергия (0-100)", min_value=0, max_value=100, value=50)
                new_stability = st.number_input("Стабильность (0.0-1.0)", min_value=0.0, max_value=1.0, value=0.5, step=0.1)
                new_creatures = st.number_input("Количество существ внутри", min_value=0, max_value=1000, value=0)
                submitted = st.form_submit_button("Добавить портал")

                if submitted:
                    if not new_name:
                        st.session_state.create_message = ("error", "Название не может быть пустым")
                        st.rerun()
                    else:
                        all_names = [p["name"] for p in portals] + [a["name"] for a in archive]
                        if new_name in all_names:
                            st.session_state.create_message = ("error", f"Портал с именем «{new_name}» уже существует")
                            st.rerun()
                        else:
                            portals.append({
                                "name": new_name,
                                "world": new_world,
                                "energy": new_energy,
                                "stability": new_stability,
                                "status": "открыт",
                                "creatures": new_creatures
                            })
                            add_log(f"создан портал: {new_name}")
                            save_json(PORTALS_FILE, portals)
                            st.session_state.create_message = ("success", f"Портал «{new_name}» создан")
                            st.rerun()


elif st.session_state.page == "Журнал":

    st.header("Журнал событий")

    if role != "admin":
        st.info("Доступно только мастеру порталов")
    else:
        search = st.text_input("Поиск по тексту записи")

        col_date1, col_date2 = st.columns(2)
        with col_date1:
            date_from = st.date_input("С", value=None)
        with col_date2:
            date_to = st.date_input("По", value=None)

        filtered_entries = []
        for entry in log:
            if not isinstance(entry, dict):
                continue
            text = entry.get("text", "")
            dt_str = entry.get("datetime", "")
            if search and search.lower() not in text.lower():
                continue
            try:
                entry_date = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                continue
            if date_from and entry_date < date_from:
                continue
            if date_to and entry_date > date_to:
                continue
            filtered_entries.append(entry)

        if not filtered_entries:
            st.info("Записей по фильтру не найдено")
        else:
            filtered_entries = list(reversed(filtered_entries))
            recent = filtered_entries[:10]
            older = filtered_entries[10:]

            for entry in recent:
                dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M:%S")
                st.write(f"{dt.strftime('%d.%m.%Y %H:%M:%S')} — {entry['text']}")

            if older:
                with st.expander(f"Показать более ранние записи ({len(older)})"):
                    with st.container(height=300):
                        for entry in older:
                            dt = datetime.strptime(entry["datetime"], "%Y-%m-%d %H:%M:%S")
                            st.write(f"{dt.strftime('%d.%m.%Y %H:%M:%S')} — {entry['text']}")


elif st.session_state.page == "AI Worklog":

    st.markdown(load_worklog())
