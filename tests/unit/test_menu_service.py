"""Unit tests for menu_service.py with mocked MenuRepository."""
import unittest
from unittest.mock import MagicMock, patch


class TestGetFullMenu(unittest.TestCase):

    def setUp(self):
        self.repo_patcher = patch('src.services.menu_service.MenuRepository')
        self.MockRepo = self.repo_patcher.start()
        self.mock_repo = MagicMock()
        self.MockRepo.return_value = self.mock_repo

        from src.services.menu_service import MenuService
        self.service = MenuService()

    def tearDown(self):
        self.repo_patcher.stop()

    def test_returns_organized_by_category(self):
        self.mock_repo.get_all_categories.return_value = [
            {'category_id': 1, 'cat_name': 'Mains'},
            {'category_id': 2, 'cat_name': 'Desserts'},
        ]
        self.mock_repo.get_all_items.return_value = [
            {'kic_id': 1, 'kic_name': 'Curry', 'category_id': 1},
            {'kic_id': 2, 'kic_name': 'Cake', 'category_id': 2},
        ]

        result = self.service.get_full_menu()

        self.assertIn('categories', result)
        self.assertIn('items_by_category', result)
        self.assertIn(1, result['items_by_category'])
        self.assertIn(2, result['items_by_category'])
        self.assertEqual(result['items_by_category'][1][0]['kic_name'], 'Curry')

    def test_passes_category_filter(self):
        self.mock_repo.get_all_categories.return_value = []
        self.mock_repo.get_all_items.return_value = []

        self.service.get_full_menu(category_id=3)

        self.mock_repo.get_all_items.assert_called_once_with(
            category_id=3, is_catering=None, is_active=True
        )

    def test_passes_catering_filter(self):
        self.mock_repo.get_all_categories.return_value = []
        self.mock_repo.get_all_items.return_value = []

        self.service.get_full_menu(is_catering=True)

        self.mock_repo.get_all_items.assert_called_once_with(
            category_id=None, is_catering=True, is_active=True
        )

    def test_empty_menu(self):
        self.mock_repo.get_all_categories.return_value = []
        self.mock_repo.get_all_items.return_value = []

        result = self.service.get_full_menu()

        self.assertEqual(result['categories'], [])
        self.assertEqual(result['items_by_category'], {})


class TestCreateItem(unittest.TestCase):

    def setUp(self):
        self.repo_patcher = patch('src.services.menu_service.MenuRepository')
        self.MockRepo = self.repo_patcher.start()
        self.mock_repo = MagicMock()
        self.MockRepo.return_value = self.mock_repo

        from src.services.menu_service import MenuService
        self.service = MenuService()

    def tearDown(self):
        self.repo_patcher.stop()

    def test_create_success(self):
        self.mock_repo.create_item.return_value = 42

        ok, msg, item_id = self.service.create_item(
            name='Biryani', price=12.99, category_id=1
        )

        self.assertTrue(ok)
        self.assertEqual(item_id, 42)

    def test_negative_price_rejected(self):
        ok, msg, item_id = self.service.create_item(
            name='Biryani', price=-1.00, category_id=1
        )

        self.assertFalse(ok)
        self.assertIsNone(item_id)
        self.mock_repo.create_item.assert_not_called()

    def test_zero_price_allowed(self):
        self.mock_repo.create_item.return_value = 43

        ok, msg, item_id = self.service.create_item(
            name='Free Item', price=0, category_id=1
        )

        self.assertTrue(ok)

    def test_repo_returns_none_is_failure(self):
        self.mock_repo.create_item.return_value = None

        ok, msg, item_id = self.service.create_item(
            name='Biryani', price=10.00, category_id=1
        )

        self.assertFalse(ok)
        self.assertIsNone(item_id)


class TestUpdateItem(unittest.TestCase):

    def setUp(self):
        self.repo_patcher = patch('src.services.menu_service.MenuRepository')
        self.MockRepo = self.repo_patcher.start()
        self.mock_repo = MagicMock()
        self.MockRepo.return_value = self.mock_repo

        from src.services.menu_service import MenuService
        self.service = MenuService()

    def tearDown(self):
        self.repo_patcher.stop()

    def test_update_success(self):
        self.mock_repo.update_item.return_value = True

        ok, msg = self.service.update_item(kic_id=1, name='New Name')

        self.assertTrue(ok)

    def test_update_failure_returns_false(self):
        self.mock_repo.update_item.return_value = False

        ok, msg = self.service.update_item(kic_id=999, name='New Name')

        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
