import numpy as np

class Shield:
    def __init__(self, name, req_lev, option1=0, option2=0, _type='shield', init_upgrade=0, break_point=False,
                 success=0):
        self.name = name  # 아이템 이름
        self.req_lev = req_lev  # 제한 레벨
        self.option1 = option1  # 물리방어력
        self.option2 = option2  # 마법방어력
        self._type = _type  # 아이템 종류
        self.possible_upgrade = init_upgrade  # 업그레이드 가능 횟수
        self.break_point = break_point  # 강화 중단
        self.success = success  # 성공횟수

    def enhance(self, scroll, message='강화 실패'):
        self.message = message
        if scroll._type == self._type:  # 같은 종류일 때 강화 시도
            if self.possible_upgrade > 0:  # 잔여 업그레이드 가능 수 확인
                if np.random.binomial(1, scroll.p) == 1:  # 강화 확률
                    self.option1 += scroll.option1  # 옵션 강화
                    self.option2 += scroll.option1  # 옵션 강화
                    self.message = '강화 성공'
                    self.success += 1  # 성공 횟수
                self.possible_upgrade -= 1


            else:
                print('가능한 업그레이드 횟수를 초과하였습니다.')
                self.break_point = True
        else:
            print('해당 아이템에는 사용할 수 없습니다.')

    def call_option(self):
        if not self.break_point:
            print('[{}] 물리방어력: +{}, 마법방어력: +{}, 업그레이드 가능 횟수: {}, 강화 성공 횟수: {}'
                  .format(self.message, str(self.option1), str(self.option2), str(self.possible_upgrade),
                          str(self.success)))

    def __str__(self):
        return self.name


class Scroll:
    def __init__(self, name, p, option1, option2, _type):
        self.name = name  # 아이템 이름
        self.p = p  # 강화 확률
        self.option1 = option1  # 물리방어력 증가 옵션
        self.option2 = option2  # 마법방어력 증가 옵션
        self._type = _type  # 아이템 종류

    def __str__(self):
        return self.name

p = 0.5
scroll = Scroll('방패 방어력 {}% 주문서'.format(str(p*100)), p, 20, 10, 'shield')

print('*강화 주문서 :',scroll)
count_list=[]
for i in range(0,30):
    print('-----------%d번째 item-----------' %(i+1))
    namddoo = Shield('냄비뚜껑', req_lev=10, option1=10, init_upgrade=7)
    while namddoo.possible_upgrade > 0:
        namddoo.enhance(scroll)
        namddoo.call_option()
        count_list.append(namddoo.success)
        if namddoo.break_point:
            break

print('평균 강화 성공 횟수: ',sum(count_list)/len(count_list))
print('E(X) = npq =', 7* (0.1) * (0.9))