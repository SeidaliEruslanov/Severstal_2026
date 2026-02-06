from datetime import datetime
from collections import defaultdict

# Разделитель полей во входном файле
DELIMITER = ";"

# Допустимые категории товаров
ALLOWED_CATEGORIES = {"electronics", "food", "books", "clothes"}


class ValidationError(Exception):
    """Используется для ошибок в данных"""
    pass


def parse_and_validate(line, line_number, used_ids):
    """
    Разбирает строку и проверяет корректность данных.
    В случае ошибки выбрасывает ValidationError.
    """

    parts = line.strip().split(DELIMITER)

    if len(parts) != 7:
        raise ValidationError("Неверное количество полей")

    raw_id, name, category, raw_price, raw_qty, raw_discount, raw_date = parts

    # Проверка id
    try:
        record_id = int(raw_id)
        if record_id <= 0:
            raise ValidationError("id должен быть положительным")
        if record_id in used_ids:
            raise ValidationError("id должен быть уникальным")
        used_ids.add(record_id)
    except ValueError:
        raise ValidationError("id не является числом")

    # Проверка имени
    name = name.strip()
    if len(name) < 3 or len(name) > 50:
        raise ValidationError("некорректная длина name")

    # Проверка категории
    if category not in ALLOWED_CATEGORIES:
        raise ValidationError("неизвестная категория")

    # Проверка цены
    try:
        price = float(raw_price)
        if price <= 0:
            raise ValidationError("price должен быть больше нуля")
    except ValueError:
        raise ValidationError("price имеет неверный формат")

    # Проверка количества
    try:
        quantity = int(raw_qty)
        if quantity < 0:
            raise ValidationError("quantity не может быть отрицательным")
    except ValueError:
        raise ValidationError("quantity не является целым числом")

    # Проверка скидки
    try:
        discount = float(raw_discount)
        if discount < 0 or discount > 50:
            raise ValidationError("discount вне диапазона 0–50")
    except ValueError:
        raise ValidationError("discount имеет неверный формат")

    # Логическое ограничение для food
    if category == "food" and discount > 20:
        raise ValidationError("слишком большая скидка для food")

    # Проверка даты
    try:
        created_at = datetime.strptime(raw_date, "%Y-%m-%d").date()
        if created_at > datetime.today().date():
            raise ValidationError("дата указана в будущем")
    except ValueError:
        raise ValidationError("неверный формат даты")

    # Финальная цена с учётом скидки
    final_price = price * (1 - discount / 100)

    if final_price < 1:
        raise ValidationError("итоговая цена меньше 1")

    return {
        "id": record_id,
        "name": name,
        "category": category,
        "final_price": round(final_price, 2),
        "quantity": quantity,
        "total_value": round(final_price * quantity, 2)
    }


def process_file(path):
    """
    Читает файл, разделяет записи на корректные и ошибочные.
    """
    valid_records = []
    errors = []
    used_ids = set()

    try:
        with open(path, encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    errors.append((line_number, "пустая строка"))
                    continue

                try:
                    record = parse_and_validate(line, line_number, used_ids)
                    valid_records.append(record)
                except ValidationError as e:
                    errors.append((line_number, str(e)))
    except FileNotFoundError:
        print("Файл input.txt не найден")
        return [], []

    return valid_records, errors


def calculate_statistics(records):
    """
    Считает агрегированную статистику по корректным данным.
    """
    stats = {
        "total_value": 0.0,
        "avg_price": 0.0,
        "by_category": defaultdict(lambda: {"count": 0, "value": 0.0})
    }

    if not records:
        return stats

    stats["total_value"] = sum(r["total_value"] for r in records)
    stats["avg_price"] = sum(r["final_price"] for r in records) / len(records)

    for r in records:
        cat = stats["by_category"][r["category"]]
        cat["count"] += 1
        cat["value"] += r["total_value"]

    return stats


def generate_report(valid, errors, stats):
    """
    Формирует текст отчёта для записи в файл.
    """
    lines = [
        "ОТЧЁТ ОБРАБОТКИ ДАННЫХ",
        "=" * 50,
        f"Всего записей: {len(valid) + len(errors)}",
        f"Корректных записей: {len(valid)}",
        f"Некорректных записей: {len(errors)}",
        "",
        f"Суммарная стоимость товаров: {stats['total_value']:.2f}",
        f"Средняя финальная цена: {stats['avg_price']:.2f}",
        "",
        "СТАТИСТИКА ПО КАТЕГОРИЯМ:"
    ]

    for category, data in stats["by_category"].items():
        lines.append(
            f"- {category}: {data['count']} шт., стоимость {data['value']:.2f}"
        )

    lines.append("")
    lines.append("ОШИБКИ:")
    if not errors:
        lines.append("Ошибок не обнаружено.")
    else:
        for line_num, msg in errors:
            lines.append(f"Строка {line_num}: {msg}")

    return "\n".join(lines)


def main():
    input_file = "input.txt"
    output_file = "report.txt"

    valid, errors = process_file(input_file)
    stats = calculate_statistics(valid)
    report = generate_report(valid, errors, stats)

    # Запись отчёта в файл
    with open(output_file, "w", encoding="utf-8") as file:
        file.write(report)

    # Вывод краткой информации в консоль
    print("УТИЛИТА ОБРАБОТКИ ДАННЫХ")
    print("=" * 40)
    print(f"Всего записей: {len(valid) + len(errors)}")
    print(f"Корректных: {len(valid)}")
    print(f"Некорректных: {len(errors)}")
    print(f"Суммарная стоимость: {stats['total_value']:.2f}")
    print(f"Отчёт сохранён в файл: {output_file}")


if __name__ == "__main__":
    main()
