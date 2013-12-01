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

class RepositoryDuplicateDefinitionTests(unittest.TestCase):
    def _add_validation(self, repository, mark):
        @repository.config(mark, "id", optionals=["id"])
        def callback(data, id=1):
            pass

    def test_it(self):
        from block.form.validation import validation_repository_factory
        repository = validation_repository_factory()
        mark = object()

        self.assertEqual(len(repository[mark].validators), 0)
        self._add_validation(repository, mark)
        self.assertEqual(len(repository[mark].validators), 1)
        self._add_validation(repository, mark)
        self.assertEqual(len(repository[mark].validators), 1)
        self._add_validation(repository, mark)
        self.assertEqual(len(repository[mark].validators), 1)

if __name__ == '__main__':
    unittest.main()
