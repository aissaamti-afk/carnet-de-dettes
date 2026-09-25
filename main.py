# -*- coding: utf-8 -*-

import json
import os
import re
import shutil
from datetime import datetime

from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse, Rectangle
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView


CUSTOMERS = []
FONT = None

# =========================================================
# PALETTE
# =========================================================

BG = (0.055, 0.075, 0.11, 1)
CARD = (0.10, 0.125, 0.18, 1)
CARD_LIGHT = (0.12, 0.15, 0.21, 1)
WHITE = (0.96, 0.97, 1, 1)
MUTED = (0.63, 0.68, 0.76, 1)
BLUE = (0.08, 0.42, 0.82, 1)
BLUE_DARK = (0.055, 0.30, 0.62, 1)
GREEN = (0.08, 0.58, 0.30, 1)
ORANGE = (0.88, 0.38, 0.08, 1)
RED = (0.72, 0.16, 0.19, 1)
BORDER = (0.20, 0.25, 0.34, 1)


# =========================================================
# OUTILS
# =========================================================

def font_path():
    app = App.get_running_app()
    paths = []

    if app:
        paths.append(os.path.join(app.directory, "fonts", "NotoSans-Regular.ttf"))

    paths.extend([
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "NotoSans-Regular.ttf"),
        "/system/fonts/NotoSans-Regular.ttf",
        "/system/fonts/Roboto-Regular.ttf",
    ])

    for path in paths:
        if os.path.exists(path):
            return path
    return None


def make_label(text="", **kwargs):
    kwargs.setdefault("halign", "center")
    kwargs.setdefault("valign", "middle")
    kwargs.setdefault("color", WHITE)

    widget = Label(text=str(text), **kwargs)

    if FONT:
        widget.font_name = FONT

    return widget


def make_button(text="", **kwargs):
    widget = ModernButton(text=str(text), **kwargs)
    if FONT:
        widget.font_name = FONT
    return widget


def set_text(widget, text):
    widget.text = str(text)


def data_path():
    app = App.get_running_app()
    folder = app.user_data_dir if app else os.path.dirname(os.path.abspath(__file__))
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "carnet_dettes_data.json")


def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def money(value):
    try:
        value = float(value)
    except Exception:
        value = 0.0

    formatted = (
        f"{value:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", " ")
    )
    return f"{formatted} DA"


def parse_amount(text):
    value = (
        str(text).strip()
        .replace(" ", "")
        .replace("\u00a0", "")
        .replace("DA", "")
        .replace("da", "")
    )

    if not value:
        raise ValueError

    if "," in value and "." in value:
        if value.rfind(",") > value.rfind("."):
            value = value.replace(".", "").replace(",", ".")
        else:
            value = value.replace(",", "")
    elif "," in value:
        parts = value.split(",")
        if len(parts) == 2 and len(parts[1]) in (1, 2):
            value = parts[0].replace(",", "") + "." + parts[1]
        else:
            value = value.replace(",", "")
    elif "." in value:
        parts = value.split(".")
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            value = value.replace(".", "")

    amount = float(value)
    if amount <= 0:
        raise ValueError
    return amount


def parse_date(value):
    try:
        return datetime.strptime(str(value), "%d/%m/%Y %H:%M")
    except Exception:
        return datetime.min


# =========================================================
# DONNÉES
# =========================================================

def load_data():
    global CUSTOMERS
    path = data_path()

    if not os.path.exists(path):
        CUSTOMERS = []
        return

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        CUSTOMERS = data if isinstance(data, list) else []
    except Exception as error:
        print("LOAD ERROR:", error)
        CUSTOMERS = []


def save_data():
    path = data_path()
    temp = path + ".tmp"
    backup = path + ".backup"

    try:
        if os.path.exists(path):
            try:
                shutil.copy2(path, backup)
            except Exception:
                pass

        with open(temp, "w", encoding="utf-8") as file:
            json.dump(CUSTOMERS, file, ensure_ascii=False, indent=2)

        os.replace(temp, path)
        return True

    except Exception as error:
        print("SAVE ERROR:", error)
        try:
            if os.path.exists(temp):
                os.remove(temp)
        except Exception:
            pass
        return False


def find_customer(query):
    query = str(query).strip().lower()

    for customer in CUSTOMERS:
        name = str(customer.get("name", "")).strip().lower()
        phone = str(customer.get("phone", "")).strip().lower()

        if query == name or (query and query == phone):
            return customer

    return None


def customer_balance(customer):
    total = 0.0

    for operation in customer.get("operations", []):
        try:
            amount = float(operation.get("amount", 0))
        except Exception:
            amount = 0.0

        if operation.get("type") == "debt":
            total += amount
        elif operation.get("type") == "payment":
            total -= amount

    return total


def total_debts():
    return sum(
        float(op.get("amount", 0))
        for customer in CUSTOMERS
        for op in customer.get("operations", [])
        if op.get("type") == "debt"
    )


def total_payments():
    return sum(
        float(op.get("amount", 0))
        for customer in CUSTOMERS
        for op in customer.get("operations", [])
        if op.get("type") == "payment"
    )


def recent_operations(limit=5):
    items = []

    for customer in CUSTOMERS:
        for operation in customer.get("operations", []):
            items.append((customer, operation))

    items.sort(
        key=lambda item: parse_date(item[1].get("date", "")),
        reverse=True
    )
    return items[:limit]


# =========================================================
# WIDGETS MODERNES
# =========================================================

class RoundedBox(BoxLayout):
    def __init__(self, bg_color=CARD, radius=18, border=False, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.radius_value = dp(radius)
        self.border = border

        with self.canvas.before:
            self.bg_color_instruction = Color(*self.bg_color)
            self.rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[self.radius_value]
            )

            if border:
                self.border_color_instruction = Color(*BORDER)
                self.border_line = Line(
                    rounded_rectangle=(
                        self.x, self.y,
                        self.width, self.height,
                        self.radius_value
                    ),
                    width=1
                )

        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _update_canvas(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.rect.radius = [self.radius_value]

        if self.border:
            self.border_line.rounded_rectangle = (
                self.x, self.y,
                self.width, self.height,
                self.radius_value
            )


class ModernButton(Button):
    def __init__(self, bg_color=BLUE, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = WHITE
        self.font_size = dp(15)
        self.bold = True

        with self.canvas.before:
            self.btn_color = Color(*self.bg_color)
            self.btn_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )

        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.btn_rect.pos = self.pos
        self.btn_rect.size = self.size


class ModernTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = WHITE
        self.hint_text_color = MUTED
        self.cursor_color = WHITE
        self.padding = [dp(14), dp(12), dp(14), dp(12)]
        self.font_size = dp(14)
        if FONT:
            self.font_name = FONT

        with self.canvas.before:
            self.input_color = Color(*CARD_LIGHT)
            self.input_rect = RoundedRectangle(
                pos=self.pos,
                size=self.size,
                radius=[dp(14)]
            )
            self.input_border_color = Color(*BORDER)
            self.input_border = Line(
                rounded_rectangle=(
                    self.x, self.y, self.width, self.height, dp(14)
                ),
                width=1
            )

        self.bind(pos=self._sync_input, size=self._sync_input)

    def _sync_input(self, *_):
        self.input_rect.pos = self.pos
        self.input_rect.size = self.size
        self.input_border.rounded_rectangle = (
            self.x, self.y, self.width, self.height, dp(14)
        )



class NavIcon(Widget):
    """Icône vectorielle dessinée par Kivy Canvas : aucune police/emoji."""
    def __init__(self, icon_type="home", active=False, **kwargs):
        super().__init__(**kwargs)
        self.icon_type = icon_type
        self.active = active
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        cx, cy = x + w / 2, y + h / 2
        c = WHITE if self.active else MUTED
        with self.canvas:
            Color(*c)
            if self.icon_type == "home":
                Line(points=[cx-dp(10),cy, cx,cy+dp(9), cx+dp(10),cy], width=1.8)
                Line(rectangle=(cx-dp(8),cy-dp(9),dp(16),dp(14)), width=1.8)
            elif self.icon_type == "clients":
                Ellipse(pos=(cx-dp(10),cy+dp(2)), size=(dp(7),dp(7)))
                Ellipse(pos=(cx+dp(3),cy+dp(2)), size=(dp(7),dp(7)))
                Line(points=[cx-dp(13),cy-dp(7),cx-dp(2),cy-dp(7)], width=1.8)
                Line(points=[cx+dp(1),cy-dp(7),cx+dp(12),cy-dp(7)], width=1.8)
            elif self.icon_type == "add":
                Line(points=[cx-dp(9),cy,cx+dp(9),cy], width=2.4)
                Line(points=[cx,cy-dp(9),cx,cy+dp(9)], width=2.4)
            elif self.icon_type == "stats":
                Line(points=[cx-dp(12),cy-dp(10),cx-dp(12),cy+dp(1)], width=2.5)
                Line(points=[cx,cy-dp(10),cx,cy+dp(7)], width=2.5)
                Line(points=[cx+dp(12),cy-dp(10),cx+dp(12),cy+dp(12)], width=2.5)
            elif self.icon_type == "more":
                Ellipse(pos=(cx-dp(3),cy+dp(7)), size=(dp(6),dp(6)))
                Ellipse(pos=(cx-dp(3),cy-dp(3)), size=(dp(6),dp(6)))
                Ellipse(pos=(cx-dp(3),cy-dp(13)), size=(dp(6),dp(6)))

class NavItem(ButtonBehavior, BoxLayout):
    """Barre inférieure stable : icône Canvas + texte, sans Emoji."""
    def __init__(self, icon_type, text, callback, active=False, **kwargs):
        super().__init__(orientation="vertical", spacing=dp(1), padding=(dp(2),dp(3)), **kwargs)
        self.callback = callback
        self.icon = NavIcon(icon_type=icon_type, active=active, size_hint_y=None, height=dp(31))
        self.label = make_label(text, color=WHITE if active else MUTED, font_size=dp(10.5), bold=active, size_hint_y=None, height=dp(22))
        self.add_widget(self.icon)
        self.add_widget(self.label)
        with self.canvas.before:
            self.active_color = Color(*(BLUE_DARK if active else (0,0,0,0)))
            self.active_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._sync, size=self._sync)

    def _sync(self, *_):
        self.active_rect.pos = self.pos
        self.active_rect.size = self.size

    def on_release(self):
        self.callback()

class StatCard(RoundedBox):
    def __init__(self, title, value, accent=BLUE, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(dp(10), dp(8)),
            spacing=dp(2),
            bg_color=CARD,
            border=True,
            **kwargs
        )

        self.title_label = make_label(
            title,
            color=MUTED,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(25)
        )

        self.value_label = make_label(
            value,
            color=WHITE,
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(34)
        )

        self.add_widget(self.title_label)
        self.add_widget(self.value_label)

    def set_value(self, value):
        self.value_label.text = str(value)


class BalanceCard(RoundedBox):
    def __init__(self, **kwargs):
        super().__init__(
            orientation="vertical",
            padding=(dp(15), dp(12)),
            spacing=dp(3),
            bg_color=BLUE,
            **kwargs
        )

        self.add_widget(make_label(
            "SOLDE RESTANT",
            color=(0.86, 0.93, 1, 1),
            font_size=dp(13),
            size_hint_y=None,
            height=dp(24)
        ))

        self.add_widget(make_label(
            "Montant total à récupérer",
            color=(0.78, 0.88, 1, 1),
            font_size=dp(11),
            size_hint_y=None,
            height=dp(20)
        ))

        self.value_label = make_label(
            "0 DA",
            color=WHITE,
            font_size=dp(28),
            bold=True,
            size_hint_y=None,
            height=dp(48)
        )
        self.add_widget(self.value_label)

    def set_value(self, value):
        self.value_label.text = str(value)


class SectionTitle(Label):
    def __init__(self, text="", **kwargs):
        super().__init__(
            text=text,
            color=WHITE,
            font_size=dp(17),
            bold=True,
            halign="left",
            valign="middle",
            **kwargs
        )
        if FONT:
            self.font_name = FONT


# =========================================================
# APPLICATION
# =========================================================

class DebtBook(App):

    title = "Carnet de dettes"

    def build(self):
        global FONT
        FONT = font_path()
        load_data()

        Window.clearcolor = BG

        self.root_layout = BoxLayout(
            orientation="vertical",
            padding=(dp(12), dp(8), dp(12), dp(8)),
            spacing=dp(8)
        )

        self.content = BoxLayout(
            orientation="vertical",
            spacing=dp(8)
        )

        self.root_layout.add_widget(self.content)

        self.bottom_nav = self.build_bottom_nav()
        self.root_layout.add_widget(self.bottom_nav)

        self.show_home()
        return self.root_layout

    # =====================================================
    # NAVIGATION
    # =====================================================

    def build_bottom_nav(self):
        nav = RoundedBox(
            orientation="horizontal",
            padding=(dp(6), dp(5)),
            spacing=dp(5),
            size_hint_y=None,
            height=dp(82),
            bg_color=(0.025, 0.045, 0.075, 1),
            radius=18
        )

        items = [
            ("home", "Accueil", self.show_home),
            ("clients", "Clients", self.show_customers_page),
            ("add", "Ajouter", self.show_add_page),
            ("stats", "Statistiques", self.show_statistics_page),
            ("more", "Plus", self.show_more_page),
        ]

        for icon_type, text, callback in items:
            item = NavItem(
                icon_type=icon_type,
                text=text,
                callback=callback,
                size_hint_x=1,
                size_hint_y=1
            )
            nav.add_widget(item)

        return nav

    def clear_content(self):
        self.content.clear_widgets()

    # =====================================================
    # ACCUEIL
    # =====================================================

    def show_home(self, *_):
        self.clear_content()

        scroll = ScrollView(
            do_scroll_x=False
        )

        page = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(4), dp(4)),
            size_hint_y=None
        )
        page.bind(minimum_height=page.setter("height"))

        page.add_widget(make_label(
            "Carnet de dettes",
            color=WHITE,
            font_size=dp(27),
            bold=True,
            size_hint_y=None,
            height=dp(42)
        ))

        page.add_widget(make_label(
            "Gestion simple de vos comptes clients",
            color=MUTED,
            font_size=dp(13),
            size_hint_y=None,
            height=dp(24)
        ))

        page.add_widget(make_label(
            f"Dernière mise à jour : {now()}",
            color=MUTED,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(22)
        ))

        self.balance_card = BalanceCard(
            size_hint_y=None,
            height=dp(132)
        )
        page.add_widget(self.balance_card)

        stats = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(148)
        )

        self.card_clients = StatCard(
            "Clients", "0",
            size_hint_y=None,
            height=dp(70)
        )
        self.card_debtors = StatCard(
            "Débiteurs", "0",
            size_hint_y=None,
            height=dp(70)
        )
        self.card_debts = StatCard(
            "Total des dettes", "0 DA",
            size_hint_y=None,
            height=dp(70)
        )
        self.card_payments = StatCard(
            "Paiements", "0 DA",
            size_hint_y=None,
            height=dp(70)
        )

        for card in (
            self.card_clients,
            self.card_debtors,
            self.card_debts,
            self.card_payments
        ):
            stats.add_widget(card)

        page.add_widget(stats)

        page.add_widget(SectionTitle(
            "Actions rapides",
            size_hint_y=None,
            height=dp(35)
        ))

        actions = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(126)
        )

        quick = [
            ("Ajouter un client", self.add_customer, BLUE),
            ("Ajouter une dette", self.add_debt, ORANGE),
            ("Enregistrer un paiement", self.add_payment, GREEN),
            ("Voir les débiteurs", self.show_debtors, RED),
        ]

        for text, callback, color in quick:
            b = make_button(
                text,
                bg_color=color,
                size_hint_y=None,
                height=dp(59)
            )
            b.bind(on_release=callback)
            actions.add_widget(b)

        page.add_widget(actions)

        page.add_widget(SectionTitle(
            "Activité récente",
            size_hint_y=None,
            height=dp(35)
        ))

        recent = recent_operations(5)

        if not recent:
            page.add_widget(make_label(
                "Aucune activité récente.",
                color=MUTED,
                size_hint_y=None,
                height=dp(50)
            ))
        else:
            for customer, operation in recent:
                kind = (
                    "Dette"
                    if operation.get("type") == "debt"
                    else "Paiement"
                )
                amount = money(operation.get("amount", 0))
                date = operation.get("date", "")

                activity = RoundedBox(
                    orientation="horizontal",
                    padding=(dp(12), dp(5)),
                    bg_color=CARD,
                    border=True,
                    size_hint_y=None,
                    height=dp(62)
                )

                info = BoxLayout(
                    orientation="vertical"
                )

                info.add_widget(make_label(
                    f"{customer.get('name', '')}  •  {kind}  •  {amount}",
                    halign="left",
                    color=WHITE,
                    font_size=dp(13)
                ))

                info.add_widget(make_label(
                    date,
                    halign="left",
                    color=MUTED,
                    font_size=dp(11)
                ))

                activity.add_widget(info)
                page.add_widget(activity)

        page.add_widget(Widget(size_hint_y=None, height=dp(12)))

        scroll.add_widget(page)
        self.content.add_widget(scroll)
        self.refresh()

    # =====================================================
    # REFRESH
    # =====================================================

    def refresh(self, message="Données mises à jour"):
        if hasattr(self, "balance_card"):
            remaining = sum(
                customer_balance(c)
                for c in CUSTOMERS
            )

            self.balance_card.set_value(money(remaining))
            self.card_clients.set_value(len(CUSTOMERS))
            self.card_debtors.set_value(sum(
                1 for c in CUSTOMERS
                if customer_balance(c) > 0
            ))
            self.card_debts.set_value(money(total_debts()))
            self.card_payments.set_value(money(total_payments()))

    # =====================================================
    # PAGE CLIENTS
    # =====================================================

    def show_customers_page(self, *_):
        self.show_customer_page(CUSTOMERS, "Clients")

    def show_customer_page(self, customers, title):
        self.clear_content()

        root = BoxLayout(
            orientation="vertical",
            spacing=dp(9),
            padding=(dp(4), dp(2), dp(4), 0)
        )

        # En-tête
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        title_box = BoxLayout(orientation="vertical", spacing=0)
        title_box.add_widget(make_label(
            title,
            halign="left",
            font_size=dp(23),
            bold=True,
            size_hint_y=None,
            height=dp(30)
        ))
        title_box.add_widget(make_label(
            f"{len(customers)} client(s)",
            halign="left",
            color=MUTED,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(18)
        ))
        header.add_widget(title_box)

        add_btn = make_button(
            "+ Ajouter",
            size_hint_x=None,
            width=dp(105),
            size_hint_y=None,
            height=dp(43)
        )
        add_btn.bind(on_release=self.add_customer)
        header.add_widget(add_btn)
        root.add_widget(header)

        # Recherche instantanée
        search = ModernTextInput(
            hint_text="Rechercher par nom ou téléphone...",
            multiline=False,
            size_hint_y=None,
            height=dp(50)
        )
        root.add_widget(search)

        # Résumé de la page
        summary = RoundedBox(
            orientation="horizontal",
            padding=(dp(12), dp(6)),
            spacing=dp(5),
            bg_color=CARD,
            border=True,
            size_hint_y=None,
            height=dp(55)
        )

        summary_clients = make_label(
            "", halign="left", color=MUTED, font_size=dp(12)
        )
        summary_debt = make_label(
            "", halign="right", color=WHITE, font_size=dp(12), bold=True
        )
        summary.add_widget(summary_clients)
        summary.add_widget(summary_debt)
        root.add_widget(summary)

        scroll = ScrollView(do_scroll_x=False)
        grid = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=(dp(1), dp(2)),
            size_hint_y=None
        )
        grid.bind(minimum_height=grid.setter("height"))
        scroll.add_widget(grid)
        root.add_widget(scroll)
        self.content.add_widget(root)

        def render(query=""):
            q = str(query).strip().lower()
            filtered = [
                c for c in customers
                if not q
                or q in str(c.get("name", "")).lower()
                or q in str(c.get("phone", "")).lower()
            ]

            grid.clear_widgets()

            debtor_count = sum(
                1 for c in filtered if customer_balance(c) > 0
            )
            summary_clients.text = (
                f"{len(filtered)} client(s)"
                if q else f"{len(customers)} client(s)"
            )
            summary_debt.text = f"{debtor_count} débiteur(s)"

            if not filtered:
                empty = RoundedBox(
                    orientation="vertical",
                    padding=dp(16),
                    bg_color=CARD,
                    border=True,
                    size_hint_y=None,
                    height=dp(125)
                )
                empty.add_widget(make_label(
                    "Aucun client trouvé",
                    font_size=dp(17),
                    bold=True
                ))
                empty.add_widget(make_label(
                    "Essayez un autre nom ou numéro.",
                    color=MUTED,
                    font_size=dp(12)
                ))
                grid.add_widget(empty)
                return

            # Les clients avec un solde apparaissent en premier.
            ordered = sorted(
                filtered,
                key=lambda c: (customer_balance(c) <= 0, str(c.get("name", "")).lower())
            )

            for customer in ordered:
                balance = customer_balance(customer)
                card = RoundedBox(
                    orientation="horizontal",
                    padding=(dp(10), dp(8)),
                    spacing=dp(9),
                    bg_color=CARD,
                    border=True,
                    size_hint_y=None,
                    height=dp(92)
                )

                # Initiale du client
                initial = str(customer.get("name", "?"))[:1].upper() or "?"
                avatar = RoundedBox(
                    orientation="vertical",
                    padding=0,
                    bg_color=BLUE_DARK if balance > 0 else CARD_LIGHT,
                    size_hint_x=None,
                    width=dp(52)
                )
                avatar.add_widget(make_label(
                    initial,
                    font_size=dp(21),
                    bold=True,
                    color=WHITE
                ))
                card.add_widget(avatar)

                info = BoxLayout(orientation="vertical", spacing=dp(2))
                info.add_widget(make_label(
                    customer.get("name", ""),
                    halign="left",
                    font_size=dp(15),
                    bold=True,
                    size_hint_y=None,
                    height=dp(27)
                ))
                phone = customer.get("phone", "") or "Téléphone non renseigné"
                info.add_widget(make_label(
                    phone,
                    halign="left",
                    color=MUTED,
                    font_size=dp(10.5),
                    size_hint_y=None,
                    height=dp(22)
                ))
                status = "À régler" if balance > 0 else "Aucune dette"
                status_color = (0.35, 0.90, 0.55, 1) if balance <= 0 else ORANGE
                info.add_widget(make_label(
                    status,
                    halign="left",
                    color=status_color,
                    font_size=dp(10.5),
                    bold=True,
                    size_hint_y=None,
                    height=dp(22)
                ))
                card.add_widget(info)

                amount_box = BoxLayout(
                    orientation="vertical",
                    size_hint_x=None,
                    width=dp(112),
                    spacing=dp(2)
                )
                amount_box.add_widget(make_label(
                    "Solde",
                    color=MUTED,
                    font_size=dp(10),
                    size_hint_y=None,
                    height=dp(18)
                ))
                amount_box.add_widget(make_label(
                    money(balance),
                    color=ORANGE if balance > 0 else (0.35, 0.90, 0.55, 1),
                    font_size=dp(13),
                    bold=True
                ))
                open_btn = make_button(
                    "Ouvrir",
                    size_hint_y=None,
                    height=dp(37),
                    font_size=dp(12)
                )
                open_btn.bind(
                    on_release=lambda _, c=customer: self.details(c)
                )
                amount_box.add_widget(open_btn)
                card.add_widget(amount_box)

                grid.add_widget(card)

        search.bind(text=lambda _, value: render(value))
        render()

    # =====================================================
    # PAGE AJOUTER
    # =====================================================

    def show_add_page(self, *_):
        self.clear_content()

        scroll = ScrollView(do_scroll_x=False)
        page = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=(dp(4), dp(4), dp(4), dp(14)),
            size_hint_y=None
        )
        page.bind(minimum_height=page.setter("height"))

        page.add_widget(make_label(
            "Ajouter",
            halign="left",
            font_size=dp(24),
            bold=True,
            size_hint_y=None,
            height=dp(40)
        ))

        page.add_widget(make_label(
            "Choisissez l'opération à enregistrer.",
            halign="left",
            color=MUTED,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(28)
        ))

        actions = [
            (
                "AJOUTER UN CLIENT\nCréer une nouvelle fiche client",
                self.add_customer,
                BLUE
            ),
            (
                "AJOUTER UNE DETTE\nEnregistrer une nouvelle dette",
                self.add_debt,
                ORANGE
            ),
            (
                "ENREGISTRER UN PAIEMENT\nEnregistrer un règlement",
                self.add_payment,
                GREEN
            ),
        ]

        for text, callback, color in actions:
            button = make_button(
                text,
                bg_color=color,
                size_hint_y=None,
                height=dp(88),
                font_size=dp(14)
            )
            button.bind(on_release=callback)
            page.add_widget(button)

        page.add_widget(make_label(
            "Autres actions",
            halign="left",
            color=WHITE,
            font_size=dp(16),
            bold=True,
            size_hint_y=None,
            height=dp(34)
        ))

        search_button = make_button(
            "Rechercher un client",
            bg_color=CARD_LIGHT,
            size_hint_y=None,
            height=dp(60),
            font_size=dp(14)
        )
        search_button.bind(on_release=self.search)
        page.add_widget(search_button)

        page.add_widget(make_label(
            "Les données sont enregistrées automatiquement.",
            color=MUTED,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(45)
        ))

        scroll.add_widget(page)
        self.content.add_widget(scroll)

    # =====================================================
    # PAGE STATISTIQUES
    # =====================================================

    def show_statistics_page(self, *_):
        self.clear_content()

        scroll = ScrollView(do_scroll_x=False)
        page = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(4), dp(4)),
            size_hint_y=None
        )
        page.bind(minimum_height=page.setter("height"))

        page.add_widget(make_label(
            "Statistiques",
            halign="left",
            font_size=dp(24),
            bold=True,
            size_hint_y=None,
            height=dp(42)
        ))

        page.add_widget(make_label(
            "Vue d'ensemble de votre activité",
            halign="left",
            color=MUTED,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(24)
        ))

        debts = total_debts()
        payments = total_payments()
        remaining = sum(customer_balance(c) for c in CUSTOMERS)
        debtors = sum(1 for c in CUSTOMERS if customer_balance(c) > 0)
        operations = sum(
            len(c.get("operations", []))
            for c in CUSTOMERS
        )

        # Résumé principal
        summary = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(148)
        )

        cards = [
            ("Clients", str(len(CUSTOMERS))),
            ("Débiteurs", str(debtors)),
            ("Dettes", money(debts)),
            ("Paiements", money(payments)),
        ]

        for title, value in cards:
            summary.add_widget(StatCard(
                title,
                value,
                size_hint_y=None,
                height=dp(70)
            ))

        page.add_widget(summary)

        # Solde restant
        balance = RoundedBox(
            orientation="vertical",
            padding=(dp(14), dp(10)),
            spacing=dp(2),
            bg_color=BLUE,
            size_hint_y=None,
            height=dp(92)
        )
        balance.add_widget(make_label(
            "SOLDE RESTANT",
            halign="left",
            color=(0.86, 0.93, 1, 1),
            font_size=dp(11),
            size_hint_y=None,
            height=dp(22)
        ))
        balance.add_widget(make_label(
            money(remaining),
            halign="left",
            color=WHITE,
            font_size=dp(23),
            bold=True
        ))
        page.add_widget(balance)

        # Taux de recouvrement
        if debts > 0:
            rate = max(0.0, min(1.0, payments / debts))
        else:
            rate = 0.0

        rate_card = RoundedBox(
            orientation="vertical",
            padding=(dp(14), dp(10)),
            spacing=dp(7),
            bg_color=CARD,
            border=True,
            size_hint_y=None,
            height=dp(88)
        )

        rate_header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(24)
        )
        rate_header.add_widget(make_label(
            "Taux de paiement",
            halign="left",
            color=MUTED,
            font_size=dp(12)
        ))
        rate_header.add_widget(make_label(
            f"{rate * 100:.0f} %",
            halign="right",
            color=WHITE,
            font_size=dp(13),
            bold=True
        ))
        rate_card.add_widget(rate_header)

        bar = RoundedBox(
            orientation="horizontal",
            padding=0,
            bg_color=CARD_LIGHT,
            radius=8,
            size_hint_y=None,
            height=dp(12)
        )
        if rate > 0:
            fill = RoundedBox(
                orientation="horizontal",
                padding=0,
                bg_color=GREEN,
                radius=8,
                size_hint_x=rate
            )
            bar.add_widget(fill)
        if rate < 1:
            bar.add_widget(Widget(size_hint_x=max(0.0, 1.0 - rate)))
        rate_card.add_widget(bar)
        page.add_widget(rate_card)

        # Informations complémentaires
        page.add_widget(SectionTitle(
            "Activité",
            size_hint_y=None,
            height=dp(32)
        ))

        activity_card = RoundedBox(
            orientation="vertical",
            padding=(dp(12), dp(8)),
            spacing=dp(2),
            bg_color=CARD,
            border=True,
            size_hint_y=None,
            height=dp(124)
        )

        activity_rows = [
            ("Nombre d'opérations", str(operations)),
            ("Montant moyen des dettes", money(debts / sum(
                1 for c in CUSTOMERS
                for op in c.get("operations", [])
                if op.get("type") == "debt"
            )) if any(
                op.get("type") == "debt"
                for c in CUSTOMERS
                for op in c.get("operations", [])
            ) else "0 DA"),
            ("Montant moyen des paiements", money(payments / sum(
                1 for c in CUSTOMERS
                for op in c.get("operations", [])
                if op.get("type") == "payment"
            )) if any(
                op.get("type") == "payment"
                for c in CUSTOMERS
                for op in c.get("operations", [])
            ) else "0 DA"),
        ]

        for title, value in activity_rows:
            row = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(34)
            )
            row.add_widget(make_label(
                title,
                halign="left",
                color=MUTED,
                font_size=dp(11.5)
            ))
            row.add_widget(make_label(
                value,
                halign="right",
                color=WHITE,
                font_size=dp(12),
                bold=True
            ))
            activity_card.add_widget(row)

        page.add_widget(activity_card)

        # Principaux débiteurs
        page.add_widget(SectionTitle(
            "Principaux débiteurs",
            size_hint_y=None,
            height=dp(32)
        ))

        debtors_list = sorted(
            [
                c for c in CUSTOMERS
                if customer_balance(c) > 0
            ],
            key=lambda c: customer_balance(c),
            reverse=True
        )[:5]

        if not debtors_list:
            page.add_widget(make_label(
                "Aucun débiteur actuellement.",
                color=MUTED,
                size_hint_y=None,
                height=dp(50)
            ))
        else:
            for customer in debtors_list:
                row = RoundedBox(
                    orientation="horizontal",
                    padding=(dp(12), dp(6)),
                    bg_color=CARD,
                    border=True,
                    size_hint_y=None,
                    height=dp(54)
                )
                row.add_widget(make_label(
                    customer.get("name", ""),
                    halign="left",
                    font_size=dp(13),
                    bold=True
                ))
                row.add_widget(make_label(
                    money(customer_balance(customer)),
                    halign="right",
                    color=ORANGE,
                    font_size=dp(13),
                    bold=True
                ))
                page.add_widget(row)

        page.add_widget(make_label(
            "Les statistiques sont calculées automatiquement à partir des opérations enregistrées.",
            color=MUTED,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(45)
        ))

        scroll.add_widget(page)
        self.content.add_widget(scroll)

    # =====================================================
    # PAGE PLUS
    # =====================================================

    def show_more_page(self, *_):
        self.clear_content()

        scroll = ScrollView(do_scroll_x=False)
        page = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(4),
            size_hint_y=None
        )
        page.bind(minimum_height=page.setter("height"))

        page.add_widget(make_label(
            "Plus",
            halign="left",
            font_size=dp(24),
            bold=True,
            size_hint_y=None,
            height=dp(42)
        ))

        page.add_widget(make_label(
            "Outils et gestion des données",
            halign="left",
            color=MUTED,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(28)
        ))

        options = [
            ("Débiteurs", "Clients ayant un solde restant", self.show_debtors, RED),
            ("Sauvegarde / Restaurer", "Protéger ou restaurer vos données", self.backup_manager, CARD_LIGHT),
            ("Exporter un relevé PDF", "Créer un relevé détaillé pour un client", self.export_pdf_select, BLUE),
            ("À propos", "Informations sur l'application", self.about_page, CARD_LIGHT),
        ]

        for title, subtitle, callback, color in options:
            card = BoxLayout(
                orientation="vertical",
                spacing=dp(3),
                padding=(dp(16), dp(10)),
                size_hint_y=None,
                height=dp(82)
            )
            with card.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(*color)
                rect = RoundedRectangle(
                    pos=card.pos,
                    size=card.size,
                    radius=[dp(14)]
                )
            card.bind(pos=lambda w, p, r=rect: setattr(r, "pos", p))
            card.bind(size=lambda w, sz, r=rect: setattr(r, "size", sz))

            title_label = make_label(
                title,
                halign="left",
                color=WHITE,
                font_size=dp(15),
                bold=True,
                size_hint_y=None,
                height=dp(30)
            )
            subtitle_label = make_label(
                subtitle,
                halign="left",
                color=WHITE if color != CARD_LIGHT else MUTED,
                font_size=dp(11),
                size_hint_y=None,
                height=dp(28)
            )
            card.add_widget(title_label)
            card.add_widget(subtitle_label)

            button = Button(
                background_color=(0, 0, 0, 0),
                background_normal="",
                size_hint=(1, 1)
            )
            button.bind(on_release=callback)
            card.add_widget(button)
            page.add_widget(card)

        page.add_widget(make_label(
            "Vos données restent stockées localement sur l'appareil.",
            color=MUTED,
            font_size=dp(11),
            halign="center",
            size_hint_y=None,
            height=dp(50)
        ))

        scroll.add_widget(page)
        self.content.add_widget(scroll)

    def export_pdf_select(self, *_):
        if not CUSTOMERS:
            self.notify("Ajoutez d'abord un client.")
            return
        self.select_customer(self.export_pdf)

    def about_page(self, *_):
        self.clear_content()

        scroll = ScrollView(do_scroll_x=False)
        page = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=dp(8),
            size_hint_y=None
        )
        page.bind(minimum_height=page.setter("height"))

        page.add_widget(make_label(
            "À propos",
            halign="left",
            font_size=dp(24),
            bold=True,
            size_hint_y=None,
            height=dp(45)
        ))

        card = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(18),
            size_hint_y=None,
            height=dp(230)
        )
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*CARD)
            rect = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(16)])
        card.bind(pos=lambda w, p, r=rect: setattr(r, "pos", p))
        card.bind(size=lambda w, sz, r=rect: setattr(r, "size", sz))

        card.add_widget(make_label(
            "CARNET DE DETTES",
            halign="center",
            font_size=dp(22),
            bold=True,
            size_hint_y=None,
            height=dp(45)
        ))
        card.add_widget(make_label(
            "Gestion simple et moderne des dettes clients",
            halign="center",
            color=MUTED,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(32)
        ))
        card.add_widget(make_label(
            "Suivez les clients, les dettes, les paiements et les soldes depuis une seule application.",
            halign="center",
            color=WHITE,
            font_size=dp(12),
            size_hint_y=None,
            height=dp(60)
        ))
        card.add_widget(make_label(
            "Version 1.0",
            halign="center",
            color=MUTED,
            font_size=dp(11),
            size_hint_y=None,
            height=dp(25)
        ))
        page.add_widget(card)

        back = make_button(
            "Retour",
            bg_color=BLUE,
            size_hint_y=None,
            height=dp(55)
        )
        back.bind(on_release=self.show_more_page)
        page.add_widget(back)

        scroll.add_widget(page)
        self.content.add_widget(scroll)

    # =====================================================
    # CLIENT
    # =====================================================

    def add_customer(self, *_):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        name = TextInput(
            hint_text="Nom du client",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        phone = TextInput(
            hint_text="Numéro de téléphone",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        save = make_button(
            "Enregistrer le client",
            size_hint_y=None,
            height=dp(55)
        )

        box.add_widget(name)
        box.add_widget(phone)
        box.add_widget(save)

        popup = Popup(
            title="Ajouter un client",
            content=box,
            size_hint=(0.92, 0.55)
        )

        def do_save(*_):
            customer_name = name.text.strip()
            customer_phone = phone.text.strip()

            if not customer_name:
                self.notify("Le nom du client est obligatoire.")
                return

            if find_customer(customer_name):
                self.notify("Ce client existe déjà.")
                return

            customer = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "name": customer_name,
                "phone": customer_phone,
                "operations": []
            }

            CUSTOMERS.append(customer)

            if save_data():
                popup.dismiss()
                self.notify("Client ajouté avec succès.")
                self.show_home()
            else:
                CUSTOMERS.remove(customer)
                self.notify("Erreur lors de l'enregistrement.")

        save.bind(on_release=do_save)
        popup.open()

    # =====================================================
    # LISTE / CHOIX CLIENT
    # =====================================================

    def select_customer(self, callback):
        scroll = ScrollView(do_scroll_x=False)

        box = GridLayout(
            cols=1,
            spacing=dp(8),
            padding=dp(10),
            size_hint_y=None
        )
        box.bind(minimum_height=box.setter("height"))

        popup = Popup(
            title="Choisir un client",
            content=scroll,
            size_hint=(0.95, 0.85)
        )

        if not CUSTOMERS:
            box.add_widget(make_label(
                "Ajoutez d'abord un client.",
                color=MUTED,
                size_hint_y=None,
                height=dp(60)
            ))

        for customer in CUSTOMERS:
            button = make_button(
                f"{customer.get('name', '')}\nSolde : {money(customer_balance(customer))}",
                size_hint_y=None,
                height=dp(68)
            )
            button.bind(
                on_release=lambda _, c=customer:
                self.choose_customer(popup, callback, c)
            )
            box.add_widget(button)

        scroll.add_widget(box)
        popup.open()

    def choose_customer(self, popup, callback, customer):
        popup.dismiss()
        callback(customer)

    # =====================================================
    # DETTE
    # =====================================================

    def add_debt(self, *_):
        self.select_customer(self.debt_form)

    def debt_form(self, customer):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        amount = TextInput(
            hint_text="Montant : 50000 ou 50 000,50",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        note = TextInput(
            hint_text="Note facultative",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        save = make_button(
            "Enregistrer la dette",
            bg_color=ORANGE,
            size_hint_y=None,
            height=dp(55)
        )

        box.add_widget(amount)
        box.add_widget(note)
        box.add_widget(save)

        popup = Popup(
            title=f"Ajouter une dette - {customer['name']}",
            content=box,
            size_hint=(0.93, 0.62)
        )

        def do_save(*_):
            try:
                value = parse_amount(amount.text)
            except ValueError:
                self.notify("Montant incorrect.")
                return

            operation = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "type": "debt",
                "amount": value,
                "note": note.text.strip(),
                "date": now()
            }

            customer.setdefault("operations", []).append(operation)

            if save_data():
                popup.dismiss()
                self.notify("Dette enregistrée avec succès.")
                self.show_home()
            else:
                customer["operations"].remove(operation)
                self.notify("Erreur lors de l'enregistrement.")

        save.bind(on_release=do_save)
        popup.open()

    # =====================================================
    # PAIEMENT
    # =====================================================

    def add_payment(self, *_):
        self.select_customer(self.payment_form)

    def payment_form(self, customer):
        remaining = customer_balance(customer)

        if remaining <= 0:
            self.notify("Ce client n'a actuellement aucune dette.")
            return

        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        info = make_label(
            f"Solde restant : {money(remaining)}",
            color=(0.35, 0.90, 0.55, 1),
            size_hint_y=None,
            height=dp(45)
        )

        amount = TextInput(
            hint_text="Montant du paiement",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        save = make_button(
            "Enregistrer le paiement",
            bg_color=GREEN,
            size_hint_y=None,
            height=dp(55)
        )

        box.add_widget(info)
        box.add_widget(amount)
        box.add_widget(save)

        popup = Popup(
            title=f"Enregistrer un paiement - {customer['name']}",
            content=box,
            size_hint=(0.93, 0.55)
        )

        def do_save(*_):
            try:
                value = parse_amount(amount.text)
            except ValueError:
                self.notify("Montant incorrect.")
                return

            current = customer_balance(customer)

            if value > current:
                self.notify(
                    "Le paiement dépasse la dette.\n"
                    f"Maximum : {money(current)}"
                )
                return

            operation = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
                "type": "payment",
                "amount": value,
                "date": now()
            }

            customer.setdefault("operations", []).append(operation)

            if save_data():
                popup.dismiss()
                self.notify("Paiement enregistré avec succès.")
                self.show_home()
            else:
                customer["operations"].remove(operation)
                self.notify("Erreur lors de l'enregistrement.")

        save.bind(on_release=do_save)
        popup.open()

    # =====================================================
    # DÉTAILS CLIENT
    # =====================================================

    def details(self, customer, *_):
        """Page complète du client, intégrée à l'application."""
        self.clear_content()

        scroll = ScrollView(do_scroll_x=False)
        page = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=(dp(4), dp(2), dp(4), dp(12)),
            size_hint_y=None
        )
        page.bind(minimum_height=page.setter("height"))

        # En-tête avec retour
        header = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48)
        )

        back = make_button(
            "‹  Clients",
            bg_color=CARD_LIGHT,
            size_hint_x=None,
            width=dp(105),
            size_hint_y=None,
            height=dp(43),
            font_size=dp(12)
        )
        back.bind(on_release=self.show_customers_page)
        header.add_widget(back)

        header.add_widget(make_label(
            "Fiche client",
            halign="left",
            font_size=dp(22),
            bold=True
        ))
        page.add_widget(header)

        balance = customer_balance(customer)
        debts = sum(
            float(op.get("amount", 0))
            for op in customer.get("operations", [])
            if op.get("type") == "debt"
        )
        payments = sum(
            float(op.get("amount", 0))
            for op in customer.get("operations", [])
            if op.get("type") == "payment"
        )

        # Carte identité + solde
        identity = RoundedBox(
            orientation="vertical",
            padding=(dp(16), dp(12)),
            spacing=dp(3),
            bg_color=BLUE,
            size_hint_y=None,
            height=dp(145)
        )

        identity.add_widget(make_label(
            customer.get("name", ""),
            font_size=dp(23),
            bold=True,
            size_hint_y=None,
            height=dp(34)
        ))
        identity.add_widget(make_label(
            f"Téléphone : {customer.get('phone', '') or 'Non renseigné'}",
            color=(0.86, 0.93, 1, 1),
            font_size=dp(12),
            size_hint_y=None,
            height=dp(25)
        ))
        identity.add_widget(make_label(
            "SOLDE RESTANT",
            color=(0.78, 0.88, 1, 1),
            font_size=dp(11),
            size_hint_y=None,
            height=dp(20)
        ))
        identity.add_widget(make_label(
            money(balance),
            font_size=dp(25),
            bold=True,
            size_hint_y=None,
            height=dp(38)
        ))
        page.add_widget(identity)

        # Résumé financier
        financial = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(136)
        )
        financial.add_widget(StatCard(
            "Total des dettes", money(debts), accent=ORANGE,
            size_hint_y=None, height=dp(64)
        ))
        financial.add_widget(StatCard(
            "Total des paiements", money(payments), accent=GREEN,
            size_hint_y=None, height=dp(64)
        ))
        financial.add_widget(StatCard(
            "Opérations", str(len(customer.get("operations", []))), accent=BLUE,
            size_hint_y=None, height=dp(64)
        ))
        financial.add_widget(StatCard(
            "État", "À régler" if balance > 0 else "Réglé",
            accent=ORANGE if balance > 0 else GREEN,
            size_hint_y=None, height=dp(64)
        ))
        page.add_widget(financial)

        # Actions principales
        page.add_widget(SectionTitle(
            "Actions",
            size_hint_y=None,
            height=dp(32)
        ))

        actions = GridLayout(
            cols=2,
            spacing=dp(8),
            size_hint_y=None,
            height=dp(116)
        )

        debt_btn = make_button(
            "Ajouter une dette",
            bg_color=ORANGE,
            size_hint_y=None,
            height=dp(54)
        )
        payment_btn = make_button(
            "Enregistrer un paiement",
            bg_color=GREEN,
            size_hint_y=None,
            height=dp(54)
        )
        edit_btn = make_button(
            "Modifier le client",
            bg_color=BLUE,
            size_hint_y=None,
            height=dp(54)
        )
        delete_btn = make_button(
            "Supprimer le client",
            bg_color=RED,
            size_hint_y=None,
            height=dp(54)
        )

        debt_btn.bind(on_release=lambda *_: self.debt_form(customer))
        payment_btn.bind(on_release=lambda *_: self.payment_form(customer))
        edit_btn.bind(on_release=lambda *_: self.edit_customer(customer, None))
        delete_btn.bind(on_release=lambda *_: self.confirm_delete_customer(customer, None))

        for button in (debt_btn, payment_btn, edit_btn, delete_btn):
            actions.add_widget(button)
        page.add_widget(actions)

        # Exportation
        export_row = BoxLayout(
            spacing=dp(8),
            size_hint_y=None,
            height=dp(50)
        )
        export_btn = make_button(
            "Exporter PDF",
            bg_color=CARD_LIGHT,
            size_hint_y=1
        )
        share_btn = make_button(
            "Partager PDF",
            bg_color=CARD_LIGHT,
            size_hint_y=1
        )
        export_btn.bind(on_release=lambda *_: self.export_pdf(customer))
        share_btn.bind(on_release=lambda *_: self.share_pdf(customer))
        export_row.add_widget(export_btn)
        export_row.add_widget(share_btn)
        page.add_widget(export_row)

        # Historique
        page.add_widget(SectionTitle(
            "Historique des opérations",
            size_hint_y=None,
            height=dp(36)
        ))

        operations = sorted(
            customer.get("operations", []),
            key=lambda op: parse_date(op.get("date", "")),
            reverse=True
        )

        if not operations:
            empty = RoundedBox(
                orientation="vertical",
                padding=dp(15),
                bg_color=CARD,
                border=True,
                size_hint_y=None,
                height=dp(90)
            )
            empty.add_widget(make_label(
                "Aucune opération enregistrée.",
                color=MUTED,
                font_size=dp(13)
            ))
            page.add_widget(empty)
        else:
            for operation in operations:
                try:
                    amount = float(operation.get("amount", 0))
                except Exception:
                    amount = 0.0

                is_debt = operation.get("type") == "debt"
                kind = "Dette" if is_debt else "Paiement"
                color = ORANGE if is_debt else GREEN
                sign = "+" if is_debt else "−"

                card = RoundedBox(
                    orientation="horizontal",
                    padding=(dp(12), dp(7)),
                    spacing=dp(8),
                    bg_color=CARD,
                    border=True,
                    size_hint_y=None,
                    height=dp(82)
                )

                icon_box = RoundedBox(
                    orientation="vertical",
                    bg_color=color,
                    size_hint_x=None,
                    width=dp(42),
                    padding=0
                )
                icon_box.add_widget(make_label(
                    sign,
                    font_size=dp(21),
                    bold=True
                ))
                card.add_widget(icon_box)

                info = BoxLayout(orientation="vertical", spacing=0)
                info.add_widget(make_label(
                    f"{kind}  •  {money(amount)}",
                    halign="left",
                    color=color,
                    font_size=dp(13),
                    bold=True,
                    size_hint_y=None,
                    height=dp(25)
                ))
                info.add_widget(make_label(
                    operation.get("date", ""),
                    halign="left",
                    color=MUTED,
                    font_size=dp(10.5),
                    size_hint_y=None,
                    height=dp(22)
                ))
                note = operation.get("note", "")
                if note:
                    info.add_widget(make_label(
                        f"Note : {note}",
                        halign="left",
                        color=WHITE,
                        font_size=dp(9.5)
                    ))
                card.add_widget(info)

                delete = make_button(
                    "Supprimer",
                    bg_color=RED,
                    size_hint_x=None,
                    width=dp(88),
                    size_hint_y=None,
                    height=dp(40),
                    font_size=dp(10.5)
                )
                delete.bind(
                    on_release=lambda _, c=customer, o=operation:
                    self.ask_delete_operation(c, o, None)
                )
                card.add_widget(delete)
                page.add_widget(card)

        page.add_widget(Widget(size_hint_y=None, height=dp(12)))
        scroll.add_widget(page)
        self.content.add_widget(scroll)

    # =====================================================
    # SUPPRESSION OPÉRATION
    # =====================================================

    def ask_delete_operation(self, customer, operation, details_popup):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        box.add_widget(make_label(
            "Voulez-vous supprimer cette opération ?",
            font_size=dp(17)
        ))

        buttons = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(55)
        )

        yes = make_button("Oui, supprimer", bg_color=RED)
        no = make_button("Annuler", bg_color=CARD_LIGHT)

        buttons.add_widget(yes)
        buttons.add_widget(no)
        box.add_widget(buttons)

        popup = Popup(
            title="Confirmation",
            content=box,
            size_hint=(0.9, 0.42)
        )

        yes.bind(
            on_release=lambda *_:
            self.delete_operation(customer, operation, details_popup, popup)
        )
        no.bind(on_release=popup.dismiss)

        popup.open()

    def delete_operation(self, customer, operation, details_popup, confirm):
        operations = customer.get("operations", [])

        if operation not in operations:
            return

        index = operations.index(operation)
        operations.remove(operation)

        if save_data():
            confirm.dismiss()
            if details_popup:
                details_popup.dismiss()
            self.notify("Opération supprimée.")
            self.show_home()
        else:
            operations.insert(index, operation)
            self.notify("Erreur lors de la suppression.")

    # =====================================================
    # MODIFIER CLIENT
    # =====================================================

    def edit_customer(self, customer, details_popup):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        name = TextInput(
            text=customer.get("name", ""),
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        phone = TextInput(
            text=customer.get("phone", ""),
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        save = make_button(
            "Enregistrer les modifications",
            size_hint_y=None,
            height=dp(55)
        )

        box.add_widget(name)
        box.add_widget(phone)
        box.add_widget(save)

        popup = Popup(
            title="Modifier le client",
            content=box,
            size_hint=(0.92, 0.55)
        )

        def do_save(*_):
            new_name = name.text.strip()
            new_phone = phone.text.strip()

            if not new_name:
                self.notify("Le nom est obligatoire.")
                return

            other = find_customer(new_name)

            if other is not None and other is not customer:
                self.notify("Ce nom est déjà utilisé.")
                return

            old_name = customer.get("name", "")
            old_phone = customer.get("phone", "")

            customer["name"] = new_name
            customer["phone"] = new_phone

            if save_data():
                popup.dismiss()
                if details_popup:
                    details_popup.dismiss()
                self.notify("Informations du client modifiées.")
                self.show_home()
            else:
                customer["name"] = old_name
                customer["phone"] = old_phone
                self.notify("Erreur lors de l'enregistrement.")

        save.bind(on_release=do_save)
        popup.open()

    # =====================================================
    # SUPPRIMER CLIENT
    # =====================================================

    def confirm_delete_customer(self, customer, details_popup):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        box.add_widget(make_label(
            "Attention !\n"
            "Le client et toutes ses opérations seront supprimés.",
            font_size=dp(16)
        ))

        buttons = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(55)
        )

        yes = make_button("Oui, supprimer", bg_color=RED)
        no = make_button("Annuler", bg_color=CARD_LIGHT)

        buttons.add_widget(yes)
        buttons.add_widget(no)
        box.add_widget(buttons)

        confirm = Popup(
            title="Confirmation de suppression",
            content=box,
            size_hint=(0.9, 0.46)
        )

        yes.bind(
            on_release=lambda *_:
            self.delete_customer(customer, details_popup, confirm)
        )
        no.bind(on_release=confirm.dismiss)

        confirm.open()

    def delete_customer(self, customer, details_popup, confirm):
        if customer not in CUSTOMERS:
            return

        index = CUSTOMERS.index(customer)
        CUSTOMERS.remove(customer)

        if save_data():
            confirm.dismiss()
            if details_popup:
                details_popup.dismiss()
            self.notify("Client supprimé.")
            self.show_home()
        else:
            CUSTOMERS.insert(index, customer)
            self.notify("Erreur lors de la suppression.")

    # =====================================================
    # DÉBITEURS
    # =====================================================

    def show_debtors(self, *_):
        debtors = [
            (customer, customer_balance(customer))
            for customer in CUSTOMERS
            if customer_balance(customer) > 0
        ]

        debtors.sort(key=lambda item: item[1], reverse=True)
        self.show_customer_page(
            [customer for customer, _ in debtors],
            "Débiteurs"
        )

    # =====================================================
    # RECHERCHE
    # =====================================================

    def search(self, *_):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        query = TextInput(
            hint_text="Nom du client ou numéro de téléphone",
            multiline=False,
            size_hint_y=None,
            height=dp(52)
        )

        search_button = make_button(
            "Rechercher",
            size_hint_y=None,
            height=dp(55)
        )

        box.add_widget(query)
        box.add_widget(search_button)

        popup = Popup(
            title="Recherche",
            content=box,
            size_hint=(0.92, 0.45)
        )

        def do_search(*_):
            q = query.text.strip().lower()

            if not q:
                self.notify("Saisissez un nom ou un numéro de téléphone.")
                return

            results = [
                customer
                for customer in CUSTOMERS
                if q in str(customer.get("name", "")).lower()
                or q in str(customer.get("phone", "")).lower()
            ]

            popup.dismiss()

            if not results:
                self.notify("Aucun résultat.")
                return

            self.show_customer_page(results, "Résultats de recherche")

        search_button.bind(on_release=do_search)
        popup.open()

    # =====================================================
    # STATISTIQUES - COMPATIBILITÉ
    # =====================================================

    def statistics(self, *_):
        self.show_statistics_page()

    # =====================================================
    # NOTIFICATION
    # =====================================================

    def notify(self, message):
        box = BoxLayout(
            orientation="vertical",
            padding=dp(15),
            spacing=dp(10)
        )

        box.add_widget(make_label(
            message,
            font_size=dp(15)
        ))

        close = make_button(
            "Fermer",
            size_hint_y=None,
            height=dp(50)
        )
        box.add_widget(close)

        popup = Popup(
            title="Carnet de dettes",
            content=box,
            size_hint=(0.88, 0.38)
        )

        close.bind(on_release=popup.dismiss)
        popup.open()

    # =====================================================
    # SAUVEGARDE
    # =====================================================

    def create_backup_file(self, prefix="sauvegarde"):
        path = data_path()

        if not os.path.exists(path):
            return None

        folder = os.path.dirname(path)

        filename = (
            prefix + "_" +
            datetime.now().strftime("%Y%m%d_%H%M%S") +
            ".json"
        )

        backup_path = os.path.join(folder, filename)
        shutil.copy2(path, backup_path)
        return backup_path

    def backup_data(self, *_):
        try:
            if not save_data():
                self.notify("Erreur lors de la sauvegarde.")
                return

            backup_path = self.create_backup_file()

            if backup_path is None:
                self.notify("Aucune donnée à sauvegarder.")
                return

            self.notify("Sauvegarde créée avec succès.")

        except Exception as error:
            print("BACKUP ERROR:", error)
            self.notify("Erreur lors de la sauvegarde.")

    def backup_manager(self, *_):
        box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        create_button = make_button(
            "Créer une sauvegarde",
            size_hint_y=None,
            height=dp(55)
        )

        restore_button = make_button(
            "Restaurer une sauvegarde",
            size_hint_y=None,
            height=dp(55)
        )

        close_button = make_button(
            "Fermer",
            bg_color=CARD_LIGHT,
            size_hint_y=None,
            height=dp(50)
        )

        box.add_widget(create_button)
        box.add_widget(restore_button)
        box.add_widget(close_button)

        popup = Popup(
            title="Sauvegarde des données",
            content=box,
            size_hint=(0.9, 0.5)
        )

        def create_and_close(*_):
            popup.dismiss()
            self.backup_data()

        create_button.bind(on_release=create_and_close)

        restore_button.bind(
            on_release=lambda *_: (
                popup.dismiss(),
                self.show_backups()
            )
        )

        close_button.bind(on_release=popup.dismiss)
        popup.open()

    # =====================================================
    # LISTE SAUVEGARDES
    # =====================================================

    def list_backup_files(self):
        folder = os.path.dirname(data_path())

        if not os.path.isdir(folder):
            return []

        files = []

        for filename in os.listdir(folder):
            if not filename.endswith(".json"):
                continue
            if not filename.startswith("sauvegarde_"):
                continue

            full_path = os.path.join(folder, filename)

            if os.path.isfile(full_path):
                files.append(full_path)

        return sorted(files, key=os.path.getmtime, reverse=True)

    def format_backup_name(self, path):
        filename = os.path.basename(path)

        match = re.match(
            r"sauvegarde_(\d{8})_(\d{6})\.json$",
            filename
        )

        if not match:
            return filename

        date_part, time_part = match.groups()

        return (
            f"Sauvegarde du "
            f"{date_part[6:8]}/"
            f"{date_part[4:6]}/"
            f"{date_part[:4]} "
            f"à {time_part[:2]}:"
            f"{time_part[2:4]}:"
            f"{time_part[4:6]}"
        )

    def show_backups(self, *_):
        backups = self.list_backup_files()

        if not backups:
            self.notify("Aucune sauvegarde disponible.")
            return

        root = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(8)
        )

        root.add_widget(make_label(
            "Choisissez une sauvegarde à restaurer :",
            font_size=dp(15),
            size_hint_y=None,
            height=dp(45)
        ))

        scroll = ScrollView(do_scroll_x=False)

        grid = GridLayout(
            cols=1,
            spacing=dp(8),
            size_hint_y=None
        )
        grid.bind(minimum_height=grid.setter("height"))

        popup = Popup(
            title="Restaurer une sauvegarde",
            content=root,
            size_hint=(0.92, 0.8)
        )

        for backup_path in backups:
            button = make_button(
                self.format_backup_name(backup_path),
                size_hint_y=None,
                height=dp(58)
            )

            button.bind(
                on_release=lambda _, p=backup_path:
                self.confirm_restore(p, popup)
            )

            grid.add_widget(button)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        close_button = make_button(
            "Annuler",
            bg_color=CARD_LIGHT,
            size_hint_y=None,
            height=dp(50)
        )
        close_button.bind(on_release=popup.dismiss)
        root.add_widget(close_button)

        popup.open()

    # =====================================================
    # RESTAURATION
    # =====================================================

    def confirm_restore(self, backup_path, backups_popup=None):
        box = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(10)
        )

        text = (
            "Attention : les données actuelles seront remplacées "
            "par celles de cette sauvegarde.\n\n"
            "Une copie automatique sera créée avant la restauration.\n\n"
            "Voulez-vous continuer ?"
        )

        box.add_widget(make_label(text, font_size=dp(15)))

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(52),
            spacing=dp(8)
        )

        cancel = make_button("Annuler", bg_color=CARD_LIGHT)
        confirm = make_button("Restaurer", bg_color=ORANGE)

        buttons.add_widget(cancel)
        buttons.add_widget(confirm)
        box.add_widget(buttons)

        popup = Popup(
            title="Confirmer la restauration",
            content=box,
            size_hint=(0.9, 0.55)
        )

        cancel.bind(on_release=popup.dismiss)

        def do_restore(*_):
            popup.dismiss()
            if backups_popup is not None:
                backups_popup.dismiss()
            self.restore_backup(backup_path)

        confirm.bind(on_release=do_restore)
        popup.open()

    def restore_backup(self, backup_path):
        global CUSTOMERS

        if not os.path.exists(backup_path):
            self.notify("La sauvegarde sélectionnée est introuvable.")
            return

        try:
            with open(backup_path, "r", encoding="utf-8") as file:
                restored_data = json.load(file)

            if not isinstance(restored_data, list):
                raise ValueError("Format de sauvegarde invalide.")

            if not save_data():
                raise ValueError(
                    "Impossible de sauvegarder les données actuelles."
                )

            self.create_backup_file(prefix="avant_restauration")

            old_customers = CUSTOMERS
            CUSTOMERS = restored_data

            if not save_data():
                CUSTOMERS = old_customers
                save_data()
                raise ValueError(
                    "Impossible d'enregistrer la restauration."
                )

            self.show_home()
            self.notify("Sauvegarde restaurée avec succès.")

        except Exception as error:
            print("RESTORE ERROR:", error)
            self.notify(
                "Erreur : restauration impossible. "
                "Les données actuelles ont été conservées."
            )

    # =====================================================
    # PDF
    # =====================================================

    def pdf_path(self, customer):
        safe = "".join(
            character
            if character.isalnum() or character in (" ", "_", "-")
            else "_"
            for character in customer.get("name", "client")
        ).strip()

        filename = (
            f"releve_{safe}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        return os.path.join(self.user_data_dir, filename)

    def export_pdf(self, customer=None, *_):
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER, TA_RIGHT
            from reportlab.lib.units import mm
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            )

            if customer is None:
                self.notify("Sélectionnez d'abord un client.")
                return None

            pdf_path = self.pdf_path(customer)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                "TitleFR",
                parent=styles["Title"],
                fontName="Helvetica-Bold",
                fontSize=19,
                leading=23,
                alignment=TA_CENTER,
                spaceAfter=5 * mm
            )

            subtitle_style = ParagraphStyle(
                "SubtitleFR",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9,
                leading=12,
                alignment=TA_CENTER,
                textColor=colors.HexColor("#555555"),
                spaceAfter=7 * mm
            )

            section_style = ParagraphStyle(
                "SectionFR",
                parent=styles["Heading2"],
                fontName="Helvetica-Bold",
                fontSize=12,
                leading=15,
                spaceBefore=4 * mm,
                spaceAfter=3 * mm
            )

            normal_style = ParagraphStyle(
                "NormalFR",
                parent=styles["Normal"],
                fontName="Helvetica",
                fontSize=9.5,
                leading=13
            )

            right_style = ParagraphStyle(
                "RightFR",
                parent=normal_style,
                alignment=TA_RIGHT
            )

            def esc(value):
                value = "" if value is None else str(value)
                return (
                    value.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )

            operations = customer.get("operations", [])
            name = customer.get("name", "Client")
            phone = customer.get("phone", "")

            debts = []
            payments = []

            for operation in operations:
                op_type = str(operation.get("type", "")).lower()

                if op_type in ("debt", "dette"):
                    debts.append(operation)
                elif op_type in ("payment", "paiement", "payement"):
                    payments.append(operation)

            def operation_amount(operation):
                try:
                    return float(operation.get("amount", 0))
                except Exception:
                    return 0.0

            total_debt = sum(operation_amount(op) for op in debts)
            total_payment = sum(operation_amount(op) for op in payments)
            balance = total_debt - total_payment

            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=15 * mm,
                leftMargin=15 * mm,
                topMargin=16 * mm,
                bottomMargin=16 * mm,
                title="Rapport de compte client - " + name,
                author="Carnet de dettes"
            )

            story = [
                Paragraph("CARNET DE DETTES", title_style),
                Paragraph("Rapport de compte client", subtitle_style)
            ]

            client_data = [
                [
                    Paragraph("<b>Client</b>", normal_style),
                    Paragraph(esc(name), normal_style),
                    Paragraph("<b>Téléphone</b>", normal_style),
                    Paragraph(esc(phone) if phone else "—", normal_style)
                ],
                [
                    Paragraph("<b>Date du rapport</b>", normal_style),
                    Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M"), normal_style),
                    Paragraph("<b>Solde restant</b>", normal_style),
                    Paragraph(f"<b>{money(balance)}</b>", right_style)
                ]
            ]

            client_table = Table(
                client_data,
                colWidths=[28 * mm, 55 * mm, 32 * mm, 55 * mm]
            )

            client_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F3F5")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F1F3F5")),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#B8BEC5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D4D8")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ]))

            story.append(client_table)
            story.append(Spacer(1, 5 * mm))
            story.append(Paragraph("Résumé financier", section_style))

            summary_data = [
                [
                    Paragraph("<b>Total des dettes</b>", normal_style),
                    Paragraph(f"<b>{money(total_debt)}</b>", right_style)
                ],
                [
                    Paragraph("<b>Total des paiements</b>", normal_style),
                    Paragraph(f"<b>{money(total_payment)}</b>", right_style)
                ],
                [
                    Paragraph("<b>Solde restant</b>", normal_style),
                    Paragraph(f"<b>{money(balance)}</b>", right_style)
                ]
            ]

            summary_table = Table(
                summary_data,
                colWidths=[110 * mm, 60 * mm]
            )

            summary_table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#B8BEC5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D4D8")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7)
            ]))

            story.append(summary_table)
            story.append(Paragraph("Historique des opérations", section_style))

            rows = [[
                Paragraph("<b>Date</b>", normal_style),
                Paragraph("<b>Type</b>", normal_style),
                Paragraph("<b>Montant</b>", right_style),
                Paragraph("<b>Note</b>", normal_style)
            ]]

            for operation in operations:
                raw_type = str(operation.get("type", "")).lower()

                if raw_type in ("debt", "dette"):
                    operation_type = "Dette"
                elif raw_type in ("payment", "paiement", "payement"):
                    operation_type = "Paiement"
                else:
                    operation_type = str(operation.get("type", "Opération"))

                note = operation.get("note", "")

                rows.append([
                    Paragraph(esc(operation.get("date", "")), normal_style),
                    Paragraph(esc(operation_type), normal_style),
                    Paragraph(money(operation_amount(operation)), right_style),
                    Paragraph(esc(note) if note else "—", normal_style)
                ])

            if len(rows) == 1:
                rows.append([
                    Paragraph("—", normal_style),
                    Paragraph("Aucune opération", normal_style),
                    Paragraph("—", right_style),
                    Paragraph("—", normal_style)
                ])

            operations_table = Table(
                rows,
                colWidths=[34 * mm, 30 * mm, 40 * mm, 66 * mm],
                repeatRows=1
            )

            operations_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#343A40")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#B8BEC5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D4D8")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ]))

            story.append(operations_table)
            story.append(Spacer(1, 8 * mm))
            story.append(Paragraph(
                "Document généré automatiquement par Carnet de dettes.",
                subtitle_style
            ))

            def add_page_number(canvas, doc_obj):
                canvas.saveState()
                canvas.setFont("Helvetica", 8)
                canvas.setFillColor(colors.HexColor("#666666"))
                canvas.drawCentredString(
                    A4[0] / 2,
                    8 * mm,
                    f"Page {doc_obj.page}"
                )
                canvas.restoreState()

            doc.build(
                story,
                onFirstPage=add_page_number,
                onLaterPages=add_page_number
            )

            self.notify("PDF créé avec succès.")
            return pdf_path

        except ImportError:
            self.notify(
                "ReportLab n'est pas disponible pour créer le PDF."
            )
            return None

        except Exception as error:
            print("PDF ERROR:", error)
            self.notify("Erreur lors de la création du PDF.")
            return None

    # =====================================================
    # PARTAGE PDF
    # =====================================================

    def share_pdf(self, customer):
        path = self.export_pdf(customer)

        if not path:
            return

        try:
            from android import activity
            from jnius import autoclass

            FileProvider = autoclass(
                "androidx.core.content.FileProvider"
            )
            PythonActivity = autoclass(
                "org.kivy.android.PythonActivity"
            )
            Intent = autoclass(
                "android.content.Intent"
            )
            File = autoclass(
                "java.io.File"
            )

            context = PythonActivity.mActivity
            file_object = File(path)

            authority = (
                context.getPackageName()
                + ".fileprovider"
            )

            uri = FileProvider.getUriForFile(
                context,
                authority,
                file_object
            )

            intent = Intent(Intent.ACTION_SEND)
            intent.setType("application/pdf")
            intent.putExtra(Intent.EXTRA_STREAM, uri)
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)

            chooser = Intent.createChooser(
                intent,
                "Partager le relevé de dettes"
            )

            activity.startActivity(chooser)

        except Exception as error:
            print("SHARE ERROR:", error)
            self.notify(
                "PDF créé, mais le partage nécessite "
                "la configuration de FileProvider."
            )

    # =====================================================
    # ARRÊT
    # =====================================================

    def on_stop(self):
        try:
            save_data()
        except Exception:
            pass


if __name__ == "__main__":
    DebtBook().run()
