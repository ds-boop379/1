import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from datetime import datetime

DATA_FILE = 'expenses.json'

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title('Expense Tracker')
        self.root.geometry('800x550')

        # Данные
        self.expenses = []           # список словарей: {сумма, категория, дата}
        self.categories = ['Еда', 'Транспорт', 'Развлечения', 'Здоровье', 'Одежда', 'Другое']
        self.load_data()

        # --- Верхняя панель ввода ---
        input_frame = ttk.LabelFrame(root, text='Добавить расход', padding=10)
        input_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(input_frame, text='Сумма:').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text='Категория:').grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.category_var = tk.StringVar(value=self.categories[0])
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var,
                                           values=self.categories, state='readonly', width=15)
        self.category_combo.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(input_frame, text='Дата (ДД.ММ.ГГГГ):').grid(row=0, column=4, padx=5, pady=5, sticky='w')
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(input_frame, textvariable=self.date_var, width=15)
        self.date_entry.grid(row=0, column=5, padx=5, pady=5)

        add_btn = ttk.Button(input_frame, text='Добавить расход', command=self.add_expense)
        add_btn.grid(row=0, column=6, padx=10, pady=5)

        # --- Панель фильтрации и подсчёта ---
        filter_frame = ttk.LabelFrame(root, text='Фильтрация и подсчёт', padding=10)
        filter_frame.pack(fill='x', padx=10, pady=5)

        ttk.Label(filter_frame, text='Фильтр по категории:').grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.filter_category_var = tk.StringVar(value='Все')
        self.filter_category_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var,
                                                  values=['Все'] + self.categories, state='readonly', width=15)
        self.filter_category_combo.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(filter_frame, text='Дата с:').grid(row=0, column=2, padx=5, pady=5, sticky='w')
        self.filter_from_var = tk.StringVar()
        self.filter_from_entry = ttk.Entry(filter_frame, textvariable=self.filter_from_var, width=12)
        self.filter_from_entry.grid(row=0, column=3, padx=5, pady=5)

        ttk.Label(filter_frame, text='по:').grid(row=0, column=4, padx=5, pady=5)
        self.filter_to_var = tk.StringVar()
        self.filter_to_entry = ttk.Entry(filter_frame, textvariable=self.filter_to_var, width=12)
        self.filter_to_entry.grid(row=0, column=5, padx=5, pady=5)

        filter_btn = ttk.Button(filter_frame, text='Применить фильтр', command=self.apply_filter)
        filter_btn.grid(row=0, column=6, padx=10, pady=5)

        reset_btn = ttk.Button(filter_frame, text='Сбросить', command=self.reset_filters)
        reset_btn.grid(row=0, column=7, padx=10, pady=5)

        sum_btn = ttk.Button(filter_frame, text='Сумма за период', command=self.calculate_period_sum)
        sum_btn.grid(row=0, column=8, padx=10, pady=5)

        self.sum_label = ttk.Label(filter_frame, text='', foreground='blue')
        self.sum_label.grid(row=1, column=0, columnspan=9, pady=5)

        # --- Таблица расходов ---
        table_frame = ttk.Frame(root)
        table_frame.pack(fill='both', expand=True, padx=10, pady=5)

        columns = ('Сумма', 'Категория', 'Дата')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=12)
        self.tree.heading('Сумма', text='Сумма')
        self.tree.heading('Категория', text='Категория')
        self.tree.heading('Дата', text='Дата')
        self.tree.column('Сумма', width=120, anchor='center')
        self.tree.column('Категория', width=200, anchor='center')
        self.tree.column('Дата', width=150, anchor='center')

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Загружаем данные в таблицу при старте
        self.refresh_table(self.expenses)

    # ---------- Валидация ----------
    def validate_amount(self, amount_str):
        try:
            amount = float(amount_str.replace(',', '.'))
            if amount <= 0:
                return False, 'Сумма должна быть положительным числом.'
            return True, amount
        except ValueError:
            return False, 'Сумма должна быть числом.'

    def validate_date(self, date_str):
        try:
            datetime.strptime(date_str, '%d.%m.%Y')
            return True, date_str
        except ValueError:
            return False, 'Дата должна быть в формате ДД.ММ.ГГГГ (например, 01.01.2024).'

    # ---------- Добавление расхода ----------
    def add_expense(self):
        amount_raw = self.amount_var.get().strip()
        category = self.category_var.get()
        date_raw = self.date_var.get().strip()

        # Проверка заполнения
        if not amount_raw or not date_raw:
            messagebox.showwarning('Предупреждение', 'Заполните сумму и дату.')
            return

        # Валидация суммы
        valid_amt, result = self.validate_amount(amount_raw)
        if not valid_amt:
            messagebox.showerror('Ошибка', result)
            return
        amount = result

        # Валидация даты
        valid_date, result = self.validate_date(date_raw)
        if not valid_date:
            messagebox.showerror('Ошибка', result)
            return
        date = result

        # Добавляем запись
        expense = {'amount': amount, 'category': category, 'date': date}
        self.expenses.append(expense)
        self.save_data()
        self.refresh_table(self.expenses)

        # Очищаем поля
        self.amount_var.set('')
        self.date_var.set('')
        self.amount_entry.focus()

    # ---------- Фильтрация ----------
    def apply_filter(self):
        filtered = self.expenses.copy()

        # Фильтр по категории
        cat = self.filter_category_var.get()
        if cat != 'Все':
            filtered = [e for e in filtered if e['category'] == cat]

        # Фильтр по диапазону дат
        from_str = self.filter_from_var.get().strip()
        to_str = self.filter_to_var.get().strip()

        if from_str:
            valid, res = self.validate_date(from_str)
            if not valid:
                messagebox.showerror('Ошибка', f'Некорректная дата "с": {res}')
                return
            from_date = datetime.strptime(from_str, '%d.%m.%Y')
            filtered = [e for e in filtered if datetime.strptime(e['date'], '%d.%m.%Y') >= from_date]

        if to_str:
            valid, res = self.validate_date(to_str)
            if not valid:
                messagebox.showerror('Ошибка', f'Некорректная дата "по": {res}')
                return
            to_date = datetime.strptime(to_str, '%d.%m.%Y')
            filtered = [e for e in filtered if datetime.strptime(e['date'], '%d.%m.%Y') <= to_date]

        self.refresh_table(filtered)
        self.sum_label.config(text='')

    def reset_filters(self):
        self.filter_category_var.set('Все')
        self.filter_from_var.set('')
        self.filter_to_var.set('')
        self.refresh_table(self.expenses)
        self.sum_label.config(text='')

    # ---------- Подсчёт суммы за период ----------
    def calculate_period_sum(self):
        from_str = self.filter_from_var.get().strip()
        to_str = self.filter_to_var.get().strip()

        if not from_str and not to_str:
            messagebox.showinfo('Информация', 'Укажите хотя бы одну дату для периода.')
            return

        valid_from = True
        valid_to = True
        from_date = None
        to_date = None

        if from_str:
            valid, res = self.validate_date(from_str)
            if not valid:
                messagebox.showerror('Ошибка', f'Некорректная дата "с": {res}')
                return
            from_date = datetime.strptime(from_str, '%d.%m.%Y')
        if to_str:
            valid, res = self.validate_date(to_str)
            if not valid:
                messagebox.showerror('Ошибка', f'Некорректная дата "по": {res}')
                return
            to_date = datetime.strptime(to_str, '%d.%m.%Y')

        # Расчёт суммы по всем записям (можно также учитывать текущий фильтр категории, сделаем по всем)
        total = 0.0
        for e in self.expenses:
            edate = datetime.strptime(e['date'], '%d.%m.%Y')
            if from_date and edate < from_date:
                continue
            if to_date and edate > to_date:
                continue
            total += e['amount']

        self.sum_label.config(text=f'Сумма расходов за выбранный период: {total:.2f}')

    # ---------- Работа с таблицей ----------
    def refresh_table(self, data):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for exp in data:
            self.tree.insert('', 'end', values=(
                f"{exp['amount']:.2f}",
                exp['category'],
                exp['date']
            ))

    # ---------- JSON сохранение/загрузка ----------
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    self.expenses = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                self.expenses = []
        else:
            self.expenses = []

    def save_data(self):
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.expenses, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror('Ошибка сохранения', f'Не удалось сохранить данные: {e}')

if __name__ == '__main__':
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
