# -*- coding:utf-8 -*-
import unittest

class AddPickTests(unittest.TestCase):
    def _getTarget(self):
        from block.form.validation.pickup import pickup
        return pickup

    def test_it(self):
        decorator = self._getTarget()
        input_data = object()
        DBSession = object()
        login_user = object()
        @decorator(positionals=["session"], optionals=["id", ("login_user", "user")])
        def validation(data, session, id=None, user=None):
            self.assertEqual(data, input_data)
            self.assertEqual(session, DBSession)
            self.assertEqual(id, 1)
            self.assertEqual(user, login_user)
        self.assertTrue(hasattr(validation, "pick_extra"))
        validation.pick_extra(validation, input_data, {"id": 1, "session": DBSession, "login_user": login_user})

if __name__ == '__main__':
    unittest.main()
