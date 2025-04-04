from typing import List

import numpy as np


def match_pursuit(
    data: np.ndarray,
    matrix: np.ndarray,
    threshold: float = 0.01,
    max_iterations: int = 1000
) -> np.ndarray:
    """
    Реализация алгоритма Matching Pursuit для восстановления сигнала.

    :param data: Сжатый сигнал.
    :param matrix: Матрица измерений.
    :param threshold: Порог ошибки для остановки.
    :param max_iterations: Максимальное количество итераций.
    :return: Коэффициенты разложения сигнала.
    """
    if data.ndim != 1:
        raise ValueError("data должен быть одномерным массивом")
    if matrix.shape[0] != data.shape[0]:
        raise ValueError("Число строк в словаре должно совпадать с размером данных")

    # Инициализация
    residual = data.copy()
    recovered_signal = np.zeros(matrix.shape[1])
    selected_indices = []

    for _ in range(max_iterations):
        correlations = np.dot(matrix.T, residual)
        best_index = np.argmax(np.abs(correlations))
        selected_indices.append(best_index)

        step_size = correlations[best_index] / np.dot(matrix[:, best_index], matrix[:, best_index])
        recovered_signal[best_index] += step_size

        residual -= step_size * matrix[:, best_index]

        # Условие остановки
        if np.linalg.norm(residual) < threshold:
            break

    return recovered_signal


def orthogonal_match_pursuit(
    data: np.ndarray,
    matrix: np.ndarray,
    threshold: float = 0.01,
    max_iterations: int = 1000
) -> np.ndarray:
    """
    Реализация алгоритма Orthogonal Matching Pursuit для восстановления сигнала.

    :param data: Сжатый сигнал.
    :param matrix: Матрица измерений.
    :param threshold: Порог ошибки для остановки.
    :param max_iterations: Максимальное количество итераций.
    :return: Коэффициенты разложения сигнала.
    """
    if data.ndim != 1:
        raise ValueError("data должен быть одномерным массивом")
    if matrix.shape[0] != data.shape[0]:
        raise ValueError("Число строк в словаре должно совпадать с размером данных")

    # Инициализация
    residual = data.copy()
    indices = []
    recovered_signal = np.zeros(matrix.shape[1])

    for _ in range(max_iterations):
        projections = np.dot(matrix.T, residual)
        best_index = np.argmax(np.abs(projections))

        if best_index in indices:
            continue

        indices.append(best_index)

        selected_columns = matrix[:, indices]
        pseudo_inverse = np.linalg.pinv(selected_columns)
        signal_subset = np.dot(pseudo_inverse, data)
        residual = data - np.dot(selected_columns, signal_subset)

        # Условие остановки
        if np.linalg.norm(residual) < threshold:
            break

    for i, index in enumerate(indices):
        recovered_signal[index] = signal_subset[i]

    return recovered_signal


def regularized_orthogonal_match_pursuit_2(
        data: np.ndarray,
        matrix: np.ndarray,
        threshold: float = 0.01,
        max_iterations: int = 1000,
) -> np.ndarray:
    """
    Реализация Regularized Orthogonal Matching Pursuit (ROMP) для восстановления разреженного сигнала.

    Параметры:
        data: Вектор измерений (m x 1)
        matrix: Матрица измерений (m x n)
        threshold: Порог для остановки алгоритма (по норме остатка)
        max_iterations: Максимальное число итераций

    Возвращает:
        Восстановленный разреженный сигнал (n x 1)
    """
    m, n = matrix.shape
    s = n  # В оригинальном ROMP sparsity level можно оценить или задать

    # Инициализация
    residual = data.copy()
    index_set = []
    solution = np.zeros(n)

    for _ in range(max_iterations):
        # 1. Вычисление корреляционного вектора
        correlations = matrix.T @ residual

        # 2. Выбор s наибольших компонент (или всех ненулевых, если их меньше)
        magnitudes = np.abs(correlations)
        nonzero_indices = np.where(magnitudes > 0)[0]

        if len(nonzero_indices) == 0:
            break

        # Выбираем s наибольших или все ненулевые
        s_selected = min(s, len(nonzero_indices))
        largest_indices = np.argpartition(magnitudes, -s_selected)[-s_selected:]

        # 3. Регуляризация: выбор подмножества с сопоставимыми значениями
        selected_magnitudes = magnitudes[largest_indices]
        max_magnitude = np.max(selected_magnitudes)

        # Находим индексы, где значения не менее половины максимального
        J0 = largest_indices[selected_magnitudes >= 0.5 * max_magnitude]

        # Если J0 пусто, берем индекс с максимальным значением
        if len(J0) == 0:
            J0 = [np.argmax(magnitudes)]

        # 4. Добавляем новые индексы в множество (исключая уже выбранные)
        new_indices = [idx for idx in J0 if idx not in index_set]
        if not new_indices:
            break

        index_set.extend(new_indices)
        index_set = list(set(index_set))  # Удаляем дубликаты

        # 5. Обновляем решение методом наименьших квадратов
        submatrix = matrix[:, index_set]
        solution_ls = np.linalg.lstsq(submatrix, data, rcond=None)[0]

        # Обновляем полное решение
        solution = np.zeros(n)
        solution[index_set] = solution_ls

        # Обновляем остаток
        residual = data - matrix @ solution

        # Проверка условия остановки
        if np.linalg.norm(residual) < threshold:
            break

    return solution


def regularized_orthogonal_match_pursuit(
        data: np.ndarray,
        matrix: np.ndarray,
        threshold: float = 0.01,
        max_iterations: int = 1000,
) -> np.ndarray:
    """
    Реализация алгоритма Regularized Orthogonal Matching Pursuit для восстановления сигнала.

    :param data: Сжатый сигнал.
    :param matrix: Матрица измерений.
    :param threshold: Порог ошибки для остановки.
    :param max_iterations: Максимальное количество итераций.
    :return: Коэффициенты разложения сигнала.
    """
    if data.ndim != 1:
        raise ValueError("data должен быть одномерным массивом")
    if matrix.shape[0] != data.shape[0]:
        raise ValueError("Число строк в словаре должно совпадать с размером данных")

    # Инициализация
    residual = data.copy()
    indices = []
    recovered_signal = np.zeros(matrix.shape[1])
    n = matrix.shape[1]

    for _ in range(max_iterations):
        # Вычисляем проекции (скалярные произведения)
        projections = np.abs(np.dot(matrix.T, residual))
        current_s = min(len(data), len(residual))

        # Шаг 1: Выбираем top-s индексов с наибольшими проекциями
        if current_s >= n:
            J = np.arange(n)
        else:
            # Находим индексы с наибольшими проекциями (без сортировки всего массива)
            J = np.argpartition(projections, -current_s)[-current_s:]

        # Шаг 2: Находим оптимальное подмножество I в J
        I = _find_romp_subset(J, projections)

        # Если не нашли подходящее подмножество, прекращаем итерации
        if len(I) == 0:
            break

        # Добавляем новые индексы (исключая уже выбранные)
        new_indices = [idx for idx in I if idx not in indices]
        if not new_indices:
            break
        indices.extend(new_indices)

        # Обновляем решение
        selected_columns = matrix[:, indices]
        pseudo_inverse = np.linalg.pinv(selected_columns)
        signal_subset = np.dot(pseudo_inverse, data)
        residual = data - np.dot(selected_columns, signal_subset)

        # Условие остановки
        if np.linalg.norm(residual) < threshold:
            break

    # Собираем итоговый сигнал
    for i, index in enumerate(indices):
        recovered_signal[index] = signal_subset[i]

    return recovered_signal


def _find_romp_subset(J: np.ndarray, projections: np.ndarray) -> List[int]:
    """
    Вспомогательная функция для нахождения оптимального подмножества индексов по правилу ROMP.

    :param J: Множество кандидатов (индексы)
    :param projections: Вектор проекций (скалярных произведений)
    :return: Оптимальное подмножество индексов
    """
    if len(J) == 0:
        return []

    # Получаем значения проекций для кандидатов
    proj_values = projections[J]

    # Сортируем индексы по убыванию значений проекций
    sorted_indices = np.argsort(proj_values)[::-1]
    sorted_J = J[sorted_indices]
    sorted_proj = proj_values[sorted_indices]

    # Находим все возможные подмножества, удовлетворяющие условию ROMP
    candidates = []

    # Начинаем с первого элемента и пытаемся расширить подмножество
    for i in range(len(sorted_J)):
        current_val = sorted_proj[i]
        I = [sorted_J[i]]

        # Проверяем следующие элементы на соответствие условию
        for j in range(i + 1, len(sorted_J)):
            if sorted_proj[j] >= 0.5 * current_val:
                I.append(sorted_J[j])
            else:
                break

        # Проверяем условие регулярности (все элементы в I должны удовлетворять |u_i| ≤ 2|u_j|)
        if len(I) > 1:
            max_val = np.max(sorted_proj[np.isin(sorted_J, I)])
            min_val = np.min(sorted_proj[np.isin(sorted_J, I)])
            if max_val > 2 * min_val:
                continue  # Пропускаем это подмножество

        candidates.append(I)

    # Если не нашли ни одного подходящего подмножества, возвращаем максимальный элемент
    if not candidates:
        return [sorted_J[0]]

    # Выбираем подмножество с максимальной l2 нормой проекций
    best_subset = None
    max_norm = -1

    for subset in candidates:
        current_norm = np.linalg.norm(projections[subset])
        if current_norm > max_norm:
            max_norm = current_norm
            best_subset = subset

    return best_subset