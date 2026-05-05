import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

DATA_FILE = "expenses.json"

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("800x500")
        self.root.resizable(True, True)

        # Данные (список словарей)
        self.expenses = []
        self.load_data()

        # --- Поля ввода ---
        frame_input = ttk.LabelFrame(root, text="Новая запись", padding=10)
        frame_input.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_input, text="Сумма:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.amount_var = tk.StringVar()
        ttk.Entry(frame_input, textvariable=self.amount_var, width=15).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(frame_input, text="Категория:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.category_var = tk.StringVar()
        categories = ["еда", "транспорт", "развлечения", "здоровье", "образование", "другое"]
        self.category_combo = ttk.Combobox(frame_input, textvariable=self.category_var,
                                           values=categories, state="readonly", width=15)
        self.category_combo.set(categories[0])
        self.category_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        ttk.Label(frame_input, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.date_var = tk.StringVar()
        ttk.Entry(frame_input, textvariable=self.date_var, width=15).grid(row=0, column=5, padx=5, pady=5, sticky="w")

        ttk.Button(frame_input, text="Добавить расход", command=self.add_expense).grid(
            row=0, column=6, padx=10, pady=5)

        # --- Фильтры ---
        frame_filter = ttk.LabelFrame(root, text="Фильтр и итог", padding=10)
        frame_filter.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_filter, text="Категория:").pack(side="left", padx=5)
        self.filter_category_var = tk.StringVar(value="Все")
        filter_categories = ["Все"] + categories
        self.filter_category_combo = ttk.Combobox(frame_filter, textvariable=self.filter_category_var,
                                                  values=filter_categories, state="readonly", width=15)
        self.filter_category_combo.pack(side="left", padx=5)

        ttk.Label(frame_filter, text="С даты (ГГГГ-ММ-ДД):").pack(side="left", padx=5)
        self.start_date_var = tk.StringVar()
        ttk.Entry(frame_filter, textvariable=self.start_date_var, width=12).pack(side="left", padx=5)

        ttk.Label(frame_filter, text="По дату (ГГГГ-ММ-ДД):").pack(side="left", padx=5)
        self.end_date_var = tk.StringVar()
        ttk.Entry(frame_filter, textvariable=self.end_date_var, width=12).pack(side="left", padx=5)

        ttk.Button(frame_filter, text="Применить фильтр", command=self.apply_filter).pack(side="left", padx=10)
        ttk.Button(frame_filter, text="Показать все", command=self.show_all).pack(side="left", padx=5)

        # Итоговая сумма
        self.total_label = ttk.Label(frame_filter, text="Сумма: 0", font=("Arial", 10, "bold"))
        self.total_label.pack(side="right", padx=10)

        # --- Таблица (Treeview) ---
        columns = ("amount", "category", "date")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("category", text="Категория")
        self.tree.heading("date", text="Дата")
        self.tree.column("amount", width=100)
        self.tree.column("category", width=150)
        self.tree.column("date", width=120)
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Скроллбар
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Заполняем таблицу всеми данными
        self.refresh_table()

    # --- Валидация ---
    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
            return True, amount
        except ValueError:
            return False, None

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    # --- Работа с JSON ---
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.expenses = []
        else:
            self.expenses = []

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, ensure_ascii=False, indent=2)

    # --- Операции ---
    def add_expense(self):
        amount_str = self.amount_var.get().strip()
        category = self.category_var.get()
        date_str = self.date_var.get().strip()

        if not amount_str or not date_str:
            messagebox.showwarning("Предупреждение", "Все поля должны быть заполнены.")
            return

        valid_amount, amount = self.validate_amount(amount_str)
        if not valid_amount:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом.")
            return

        if not self.validate_date(date_str):
            messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД (например, 2025-03-15).")
            return

        # Добавляем запись
        record = {
            "amount": amount,
            "category": category,
            "date": date_str
        }
        self.expenses.append(record)
        self.save_data()
        self.refresh_table()
        self.clear_inputs()

    def clear_inputs(self):
        self.amount_var.set("")
        self.date_var.set("")

    def refresh_table(self, data=None):
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)

        display_data = data if data is not None else self.expenses
        total = 0.0
        for rec in display_data:
            self.tree.insert("", "end", values=(rec["amount"], rec["category"], rec["date"]))
            total += rec["amount"]
        self.total_label.config(text=f"Сумма: {total:.2f}")

    def apply_filter(self):
        cat_filter = self.filter_category_var.get()
        start_str = self.start_date_var.get().strip()
        end_str = self.end_date_var.get().strip()

        # Если даты не заданы, считаем весь период
        filtered = self.expenses

        # Фильтр по категории
        if cat_filter != "Все":
            filtered = [r for r in filtered if r["category"] == cat_filter]

        # Фильтр по датам (если введены)
        if start_str and not self.validate_date(start_str):
            messagebox.showerror("Ошибка", "Начальная дата имеет неверный формат.")
            return
        if end_str and not self.validate_date(end_str):
            messagebox.showerror("Ошибка", "Конечная дата имеет неверный формат.")
            return

        if start_str:
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            filtered = [r for r in filtered if datetime.strptime(r["date"], "%Y-%m-%d") >= start_date]
        if end_str:
            end_date = datetime.strptime(end_str, "%Y-%m-%d")
            filtered = [r for r in filtered if datetime.strptime(r["date"], "%Y-%m-%d") <= end_date]

        self.refresh_table(filtered)

    def show_all(self):
        self.filter_category_var.set("Все")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.refresh_table(self.expenses)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
