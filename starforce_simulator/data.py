# data.py
import math
from typing import Dict, Union

BASE_STARFORCE_PROBABILITY: Dict[int, Dict[str, float]] = {
    # 0~11성: 파괴 없음
    0:  {'success': 0.95, 'maintain': 0.05,   'destroy': 0.00},
    1:  {'success': 0.90, 'maintain': 0.10,   'destroy': 0.00},
    2:  {'success': 0.85, 'maintain': 0.15,   'destroy': 0.00},
    3:  {'success': 0.85, 'maintain': 0.15,   'destroy': 0.00},
    4:  {'success': 0.80, 'maintain': 0.20,   'destroy': 0.00},
    5:  {'success': 0.75, 'maintain': 0.25,   'destroy': 0.00},
    6:  {'success': 0.70, 'maintain': 0.30,   'destroy': 0.00},
    7:  {'success': 0.65, 'maintain': 0.35,   'destroy': 0.00},
    8:  {'success': 0.60, 'maintain': 0.40,   'destroy': 0.00},
    9:  {'success': 0.55, 'maintain': 0.45,   'destroy': 0.00},
    10: {'success': 0.50, 'maintain': 0.50,   'destroy': 0.00},
    11: {'success': 0.45, 'maintain': 0.55,   'destroy': 0.00},
    # 12~14성: 파괴 없음 (최신 패치 반영)
    12: {'success': 0.40, 'maintain': 0.60,   'destroy': 0.00},
    13: {'success': 0.35, 'maintain': 0.65,   'destroy': 0.00},
    14: {'success': 0.30, 'maintain': 0.70,   'destroy': 0.00},
    # 15성부터 파괴 존재
    15: {'success': 0.30, 'maintain': 0.679,  'destroy': 0.021},
    16: {'success': 0.30, 'maintain': 0.679,  'destroy': 0.021},
    17: {'success': 0.15, 'maintain': 0.782,  'destroy': 0.068},
    18: {'success': 0.15, 'maintain': 0.782,  'destroy': 0.068},
    19: {'success': 0.15, 'maintain': 0.765,  'destroy': 0.085},
    20: {'success': 0.30, 'maintain': 0.595,  'destroy': 0.105},
    21: {'success': 0.15, 'maintain': 0.7225, 'destroy': 0.1275},
    22: {'success': 0.15, 'maintain': 0.68,   'destroy': 0.17},
    23: {'success': 0.10, 'maintain': 0.72,   'destroy': 0.18},
    24: {'success': 0.10, 'maintain': 0.72,   'destroy': 0.18},
    25: {'success': 0.10, 'maintain': 0.72,   'destroy': 0.18},
    26: {'success': 0.07, 'maintain': 0.744,  'destroy': 0.186},
    27: {'success': 0.05, 'maintain': 0.76,   'destroy': 0.19},
    28: {'success': 0.03, 'maintain': 0.776,  'destroy': 0.194},
    29: {'success': 0.01, 'maintain': 0.792,  'destroy': 0.198},
    30: {'success': 0.00, 'maintain': 1.00,   'destroy': 0.00}
}

COST_DIVISOR: Dict[int, int] = {
    10: 571, 11: 314, 12: 214, 13: 157, 14: 107,
    15: 200, 16: 200, 17: 150, 18: 70,  19: 45,
    20: 200, 21: 125, 22: 200, 23: 200, 24: 200,
    25: 200, 26: 200, 27: 200, 28: 200, 29: 200
}

def get_actual_probability(star: int) -> Dict[str, float]:
    """
    주어진 스타포스 수치에 대한 실제 강화 확률(성공, 유지, 파괴)을 반환합니다.
    스타캐치(성공 확률 1.05배)가 항상 성공한다고 가정한 확률입니다.
    """
    if star >= 30:
        return {'success': 0.0, 'maintain': 1.0, 'destroy': 0.0}
        
    base = BASE_STARFORCE_PROBABILITY.get(star)
    if not base:
        return {'success': 0.0, 'maintain': 1.0, 'destroy': 0.0}

    # 스타캐치 상시 적용: 성공 확률 * 1.05
    actual_success = min(1.0, base['success'] * 1.05)

    remaining_prob = 1.0 - actual_success
    base_remaining_prob = 1.0 - base['success']
    
    actual_maintain = 0.0
    actual_destroy = 0.0

    if base_remaining_prob > 0:
        actual_maintain = remaining_prob * (base['maintain'] / base_remaining_prob)
        actual_destroy = remaining_prob * (base['destroy'] / base_remaining_prob)

    return {
        'success': actual_success,
        'maintain': actual_maintain,
        'destroy': actual_destroy
    }

def calculate_base_meso_cost(level: int, current_star: int) -> int:
    """
    장비 레벨과 현재 스타포스 수치를 기반으로 1회 강화 시 필요한 기본 메소를 계산합니다.
    """
    # 장비 레벨 10 단위 버림 처리 (예: 159 → 150)
    L = math.floor(level / 10) * 10
    S = current_star
    
    cost = 0
    if 0 <= S <= 9:
        cost = 1000 + (L**3 * (S + 1)) / 36
    elif 10 <= S <= 29:
        divisor = COST_DIVISOR.get(S, 200)
        cost = 1000 + (L**3 * ((S + 1)**2.7)) / divisor
        
    # 100 단위로 반올림
    return round(cost / 100) * 100
