# games/points.py

class PointsManager:
    def __init__(self):
        # نخزن النقاط لكل لاعب باستخدام معرفه (ID)
        self.scores = {}

    def add_points(self, user_id, points):
        """إضافة نقاط للاعب"""
        if user_id not in self.scores:
            self.scores[user_id] = 0
        self.scores[user_id] += points
        return self.scores[user_id]

    def get_points(self, user_id):
        """إرجاع نقاط اللاعب"""
        return self.scores.get(user_id, 0)

    def reset_points(self, user_id=None):
        """إعادة تعيين النقاط. إذا لم يُحدد user_id، يتم إعادة تعيين جميع النقاط"""
        if user_id:
            self.scores[user_id] = 0
        else:
            self.scores = {}
