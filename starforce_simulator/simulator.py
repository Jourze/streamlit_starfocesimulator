# simulator.py
import random
from typing import Dict, Any, Union
from data import get_actual_probability, calculate_base_meso_cost

class StarForceSimulator:
    def __init__(self):
        self.level = 160
        self.current_star = 0
        self.target_star = 22
        
        # Options
        self.safeguard = False
        self.spare_cost = 0
        
        # Events
        self.shining_full = False
        self.shining_half = False
        self.sunday30 = False
        self.sunday100 = False
        self.sunday1plus1 = False
        
        # Discounts
        self.mvp_discount = 0.0
        self.pc_discount = False

        # Stats
        self.total_meso = 0
        self.total_spare_cost = 0
        self.destroy_count = 0
        self.try_count = 0

    def set_options(self, level: int = 160, target_star: int = 22, safeguard: bool = False, spare_cost: int = 0, 
                    shining_full: bool = False, shining_half: bool = False, sunday30: bool = False, sunday100: bool = False, sunday1plus1: bool = False, 
                    mvp_discount: float = 0.0, pc_discount: bool = False) -> None:
        """강화 시뮬레이션 환경(옵션)을 설정합니다."""
        self.level = level
        self.target_star = target_star
        self.safeguard = safeguard
        self.spare_cost = spare_cost
        self.shining_full = shining_full
        self.shining_half = shining_half
        self.sunday30 = sunday30
        self.sunday100 = sunday100
        self.sunday1plus1 = sunday1plus1
        self.mvp_discount = float(mvp_discount)
        self.pc_discount = pc_discount

    def get_probabilities(self, star: int) -> Dict[str, float]:
        """주어진 스타포스 단계에서의 이벤트/할인이 적용된 실제 강화 확률을 계산합니다."""
        prob = get_actual_probability(star)
        
        # 5/10/15성 100% 성공 이벤트
        if (self.sunday100 or self.shining_full) and star in [5, 10, 15]:
            return {'success': 1.0, 'maintain': 0.0, 'destroy': 0.0}

        s = prob['success']
        m = prob['maintain']
        d = prob['destroy']

        # 샤이닝 스타포스: 21성 이하 파괴 확률 30% 감소
        shining_active = self.shining_full or self.shining_half
        if shining_active and star <= 21 and d > 0:
            reduced_destroy = d * 0.3
            d -= reduced_destroy
            m += reduced_destroy 

        # 파괴 방지 (15, 16, 17성에서 적용 가능)
        if self.safeguard and 15 <= star <= 17 and d > 0:
            m += d
            d = 0.0

        return {'success': s, 'maintain': m, 'destroy': d}

    def get_cost(self, star: int) -> int:
        """현재 스타포스 수치에서 1회 강화 시 필요한 비용(할인 및 파괴 방지 적용)을 계산합니다."""
        base_cost = calculate_base_meso_cost(self.level, star)
        final_cost = float(base_cost)

        # 썬데이 메이플 30% 할인 또는 샤이닝 스타포스 (서로 중복 안됨)
        shining_active = self.shining_full or self.shining_half
        if shining_active or self.sunday30:
            final_cost -= base_cost * 0.3

        # MVP 및 PC방 할인은 17성 이하에서만 적용됨
        if star <= 17:
            discount_rate = self.mvp_discount
            if self.pc_discount:
                discount_rate += 0.05
            final_cost -= base_cost * discount_rate

        # 파괴 방지 추가 비용 (기본 비용의 100% 추가)
        if self.safeguard and 15 <= star <= 17:
            final_cost += base_cost

        return int(final_cost)

    def enhance_once(self) -> Dict[str, Any]:
        """1회 강화를 시도하고 그 결과를 반환합니다."""
        if self.current_star >= 30 or self.current_star >= self.target_star:
            return {'result': 'max', 'cost': 0, 'star': self.current_star}

        cost = self.get_cost(self.current_star)
        prob = self.get_probabilities(self.current_star)
        
        self.total_meso += cost
        self.try_count += 1

        rand = random.random()
        result = ''
        before_star = self.current_star

        if rand < prob['success']:
            result = 'success'
            self.current_star += 1
            # 1+1 이벤트
            if self.sunday1plus1 and before_star <= 10:
                self.current_star += 1
                result = 'success_1plus1'
        elif rand < prob['success'] + prob['maintain']:
            result = 'maintain'
        else:
            result = 'destroy'
            self.destroy_count += 1
            self.total_spare_cost += self.spare_cost
            # 파괴 시 12성으로 전승됨
            self.current_star = 12

        return {
            'result': result,
            'cost': cost,
            'beforeStar': before_star,
            'afterStar': self.current_star
        }

    def get_grand_total(self) -> int:
        """소모된 총 메소와 스페어(복구) 비용의 합을 반환합니다."""
        return self.total_meso + self.total_spare_cost

    def reset(self) -> None:
        """시뮬레이터 진행 상태를 초기화합니다."""
        self.current_star = 0
        self.total_meso = 0
        self.total_spare_cost = 0
        self.destroy_count = 0
        self.try_count = 0

    def get_expected_values(self, start_star: int = 0) -> Dict[str, float]:
        """목표 스타포스까지 도달하기 위한 기댓값(기대 소모 메소, 기대 파괴 횟수)을 DP를 이용해 계산합니다."""
        target = self.target_star
        
        if start_star >= target:
            return {'cost': 0, 'destroy': 0}
            
        # E_cost[i] = A_cost[i] * X + B_cost[i]
        # E_dest[i] = A_dest[i] * Y + B_dest[i]
        # where X = E_cost[12], Y = E_dest[12]
        
        A_cost = {target: 0.0}
        B_cost = {target: 0.0}
        A_dest = {target: 0.0}
        B_dest = {target: 0.0}
        
        if target > 12:
            for i in range(target - 1, 11, -1):
                prob = self.get_probabilities(i)
                cost = self.get_cost(i)
                
                p_s = prob['success']
                p_m = prob['maintain']
                p_d = prob['destroy']
                
                denom = 1.0 - p_m
                if denom == 0: denom = 1.0
                    
                A_cost[i] = (p_s * A_cost.get(i+1, 0.0) + p_d) / denom
                B_cost[i] = (cost + p_s * B_cost.get(i+1, 0.0) + p_d * self.spare_cost) / denom
                
                A_dest[i] = (p_s * A_dest.get(i+1, 0.0) + p_d) / denom
                B_dest[i] = (p_s * B_dest.get(i+1, 0.0) + p_d) / denom
                
            X = B_cost[12] / (1.0 - A_cost[12]) if (1.0 - A_cost[12]) != 0 else 0
            Y = B_dest[12] / (1.0 - A_dest[12]) if (1.0 - A_dest[12]) != 0 else 0
            
            E_cost = {i: A_cost[i] * X + B_cost[i] for i in range(12, target + 1)}
            E_dest = {i: A_dest[i] * Y + B_dest[i] for i in range(12, target + 1)}
        else:
            E_cost = {target: 0.0}
            E_dest = {target: 0.0}
            
        start_down = min(target - 1, 11)
        for i in range(start_down, start_star - 1, -1):
            prob = self.get_probabilities(i)
            cost = self.get_cost(i)
            p_s = prob['success']
            p_m = prob['maintain']
            
            denom = 1.0 - p_m
            if denom == 0: denom = 1.0
            
            after_s = i + 2 if (self.sunday1plus1 and i <= 10) else i + 1
            cost_next = E_cost.get(after_s, 0.0)
            dest_next = E_dest.get(after_s, 0.0)
            
            E_cost[i] = (cost + p_s * cost_next) / denom
            E_dest[i] = (p_s * dest_next) / denom
            
        return {'cost': E_cost[start_star], 'destroy': E_dest[start_star]}
