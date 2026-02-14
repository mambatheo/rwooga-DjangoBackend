from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()


class TestSetup(APITestCase):
    
    def setUp(self):
        # Create staff user
        self.staff_user = User.objects.create_user(
            email='staff@test.com',
            password='testpass123',
            full_name='Staff User',
            phone_number='0788111111',
            is_staff=True
        )
        
        # Create regular customer
        self.customer_user = User.objects.create_user(
            email='customer@test.com',
            password='testpass123',
            full_name='Customer User',
            phone_number='0788222222',
            is_staff=False
        )
        
        # API endpoints
        self.category_url = '/products/categories/'
        self.product_url = '/products/products/'
        self.feedback_url = '/products/feedback/'
        self.custom_request_url = '/products/custom-requests/'
        
        return super().setUp()
    
    def tearDown(self):
        return super().tearDown()